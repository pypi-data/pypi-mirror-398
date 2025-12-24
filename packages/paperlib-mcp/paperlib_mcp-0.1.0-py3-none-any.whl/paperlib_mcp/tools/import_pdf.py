"""PDF 导入工具 - 6 阶段状态机"""

import hashlib
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator

from fastmcp import FastMCP

from paperlib_mcp.db import execute_returning, get_db, query_one, query_all
from paperlib_mcp.storage import upload_file, object_exists
from paperlib_mcp.pdf_extract import extract_pdf
from paperlib_mcp.chunking import chunk_document
from paperlib_mcp.embeddings import get_embeddings_chunked, aget_embeddings_chunked
from paperlib_mcp.settings import get_settings


class IngestStage(str, Enum):
    """导入阶段"""
    HASHED = "HASHED"       # 计算 SHA256
    UPLOADED = "UPLOADED"    # 上传到 MinIO
    EXTRACTED = "EXTRACTED"  # 提取文本
    CHUNKED = "CHUNKED"      # 分块
    EMBEDDED = "EMBEDDED"    # 生成 embedding
    COMMITTED = "COMMITTED"  # 提交完成


class IngestStatus(str, Enum):
    """状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportPdfInput(BaseModel):
    """PDF 导入输入参数"""
    file_path: str
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    force: bool = False
    
    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File not found: {v}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {v}")
        return str(path.absolute())


class ImportPdfResult(BaseModel):
    """PDF 导入结果"""
    success: bool
    doc_id: str
    job_id: int | None = None
    pdf_key: str
    n_pages: int
    n_chunks: int
    embedded_chunks: int
    empty_pages: int
    skipped: bool = False
    resumed_from: str | None = None
    message: str = ""


def compute_file_sha256(file_path: str) -> str:
    """计算文件的 SHA256 哈希"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class IngestJobManager:
    """导入作业管理器"""
    
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.job_id: int | None = None
    
    def create_job(self) -> int:
        """创建新的导入作业"""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ingest_jobs (doc_id, status, current_stage)
                    VALUES (%s, %s, NULL)
                    RETURNING job_id
                    """,
                    (self.doc_id, IngestStatus.RUNNING.value)
                )
                result = cur.fetchone()
                self.job_id = result["job_id"]
                return self.job_id
    
    def get_latest_job(self) -> dict[str, Any] | None:
        """获取最新的导入作业"""
        return query_one(
            """
            SELECT job_id, status, current_stage, error
            FROM ingest_jobs
            WHERE doc_id = %s
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (self.doc_id,)
        )
    
    def get_completed_stages(self, job_id: int) -> set[str]:
        """获取已完成的阶段"""
        items = query_all(
            """
            SELECT stage FROM ingest_job_items
            WHERE job_id = %s AND status = %s
            """,
            (job_id, IngestStatus.COMPLETED.value)
        )
        return {item["stage"] for item in items}
    
    def update_stage(self, stage: IngestStage, status: IngestStatus, message: str = ""):
        """更新阶段状态"""
        if not self.job_id:
            return
        
        with get_db() as conn:
            with conn.cursor() as cur:
                # 记录阶段详情
                cur.execute(
                    """
                    INSERT INTO ingest_job_items (job_id, stage, status, message)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (self.job_id, stage.value, status.value, message)
                )
                
                # 更新作业当前阶段
                if status == IngestStatus.COMPLETED:
                    cur.execute(
                        """
                        UPDATE ingest_jobs 
                        SET current_stage = %s
                        WHERE job_id = %s
                        """,
                        (stage.value, self.job_id)
                    )
    
    def complete_job(self):
        """标记作业完成"""
        if not self.job_id:
            return
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ingest_jobs 
                    SET status = %s, finished_at = now()
                    WHERE job_id = %s
                    """,
                    (IngestStatus.COMPLETED.value, self.job_id)
                )
    
    def fail_job(self, error: str):
        """标记作业失败"""
        if not self.job_id:
            return
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ingest_jobs 
                    SET status = %s, finished_at = now(), error = %s
                    WHERE job_id = %s
                    """,
                    (IngestStatus.FAILED.value, error, self.job_id)
                )



async def import_pdf_run(
    file_path: str,
    title: str | None = None,
    authors: str | None = None,
    year: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """导入 PDF 文献到知识库 (Core Implementation)"""
    job_manager = None
    doc_id = ""
    pdf_key = ""
    
    try:
        # 1. 验证输入参数
        params = ImportPdfInput(
            file_path=file_path,
            title=title,
            authors=authors,
            year=year,
            force=force,
        )
        
        settings = get_settings()
        
        # ==================== STAGE 1: HASHED ====================
        doc_id = compute_file_sha256(params.file_path)
        pdf_key = f"papers/{doc_id}.pdf"
        
        job_manager = IngestJobManager(doc_id)
        
        # 检查是否已存在完成的导入
        existing_doc = query_one(
            "SELECT doc_id FROM documents WHERE doc_id = %s",
            (doc_id,)
        )
        
        # 检查现有的作业状态（用于断点续传）
        latest_job = job_manager.get_latest_job()
        completed_stages: set[str] = set()
        resumed_from: str | None = None
        
        if existing_doc and not params.force:
            # 文档已存在且完成，检查是否有缺失的 embedding
            stats = query_one(
                """
                SELECT COUNT(c.chunk_id) as chunks, COUNT(ce.chunk_id) as embedded
                FROM chunks c
                LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                WHERE c.doc_id = %s
                """,
                (doc_id,)
            )
            
            if stats and stats["chunks"] == stats["embedded"]:
                return ImportPdfResult(
                    success=True,
                    doc_id=doc_id,
                    pdf_key=pdf_key,
                    n_pages=0,
                    n_chunks=stats["chunks"],
                    embedded_chunks=stats["embedded"],
                    empty_pages=0,
                    skipped=True,
                    message="Document already exists with complete embeddings. Use force=True to reimport.",
                ).model_dump()
            elif stats and stats["chunks"] > stats["embedded"]:
                # 有缺失的 embedding，可以继续
                completed_stages = {
                    IngestStage.HASHED.value,
                    IngestStage.UPLOADED.value,
                    IngestStage.EXTRACTED.value,
                    IngestStage.CHUNKED.value,
                }
                resumed_from = IngestStage.CHUNKED.value
        
        elif latest_job and latest_job["status"] == IngestStatus.FAILED.value and not params.force:
            # 之前失败的作业，获取已完成的阶段
            completed_stages = job_manager.get_completed_stages(latest_job["job_id"])
            if completed_stages:
                # 找到最后完成的阶段
                stage_order = [s.value for s in IngestStage]
                for stage in reversed(stage_order):
                    if stage in completed_stages:
                        resumed_from = stage
                        break
        
        # 创建新的导入作业
        job_manager.create_job()
        
        # 记录 HASHED 阶段完成
        job_manager.update_stage(
            IngestStage.HASHED,
            IngestStatus.COMPLETED,
            f"SHA256: {doc_id}"
        )
        
        # ==================== STAGE 2: UPLOADED ====================
        if IngestStage.UPLOADED.value not in completed_stages:
            job_manager.update_stage(IngestStage.UPLOADED, IngestStatus.RUNNING)
            
            if not object_exists(pdf_key) or params.force:
                upload_file(params.file_path, pdf_key)
            
            job_manager.update_stage(
                IngestStage.UPLOADED,
                IngestStatus.COMPLETED,
                f"Uploaded to {pdf_key}"
            )
        
        # ==================== STAGE 3: EXTRACTED ====================
        pdf_result = None
        if IngestStage.EXTRACTED.value not in completed_stages:
            job_manager.update_stage(IngestStage.EXTRACTED, IngestStatus.RUNNING)
            
            pdf_result = extract_pdf(params.file_path)
            
            # 使用 PDF 元数据填充用户未指定的字段
            if pdf_result.metadata:
                if not params.title and pdf_result.metadata.title:
                    params.title = pdf_result.metadata.title
                if not params.authors and pdf_result.metadata.authors:
                    params.authors = pdf_result.metadata.authors
                if not params.year and pdf_result.metadata.year:
                    params.year = pdf_result.metadata.year
            
            job_manager.update_stage(
                IngestStage.EXTRACTED,
                IngestStatus.COMPLETED,
                f"Extracted {pdf_result.total_pages} pages, {pdf_result.empty_pages} empty"
            )
        else:
            # 即使跳过也需要提取（用于后续分块）
            pdf_result = extract_pdf(params.file_path)
            
            # 使用 PDF 元数据填充用户未指定的字段
            if pdf_result.metadata:
                if not params.title and pdf_result.metadata.title:
                    params.title = pdf_result.metadata.title
                if not params.authors and pdf_result.metadata.authors:
                    params.authors = pdf_result.metadata.authors
                if not params.year and pdf_result.metadata.year:
                    params.year = pdf_result.metadata.year
        
        # ==================== STAGE 4: CHUNKED ====================
        chunks = []
        chunk_ids = []
        
        if IngestStage.CHUNKED.value not in completed_stages:
            job_manager.update_stage(IngestStage.CHUNKED, IngestStatus.RUNNING)
            
            # 写入/更新 documents 表
            with get_db() as conn:
                with conn.cursor() as cur:
                    if existing_doc and params.force:
                        # 删除旧的 chunks 和 embeddings（级联删除）
                        cur.execute(
                            "DELETE FROM chunks WHERE doc_id = %s",
                            (doc_id,)
                        )
                        # 更新 documents
                        cur.execute(
                            """
                            UPDATE documents 
                            SET title = %s, authors = %s, year = %s, 
                                pdf_key = %s, pdf_sha256 = %s, updated_at = now()
                            WHERE doc_id = %s
                            """,
                            (
                                params.title, params.authors, params.year,
                                pdf_key, doc_id, doc_id
                            )
                        )
                    else:
                        # 插入新文档
                        cur.execute(
                            """
                            INSERT INTO documents (doc_id, title, authors, year, pdf_bucket, pdf_key, pdf_sha256)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (doc_id) DO UPDATE SET
                                title = COALESCE(EXCLUDED.title, documents.title),
                                authors = COALESCE(EXCLUDED.authors, documents.authors),
                                year = COALESCE(EXCLUDED.year, documents.year),
                                pdf_key = EXCLUDED.pdf_key,
                                pdf_sha256 = EXCLUDED.pdf_sha256,
                                updated_at = now()
                            """,
                            (
                                doc_id, params.title, params.authors, params.year,
                                settings.s3_bucket, pdf_key, doc_id
                            )
                        )
            
            # 分块
            pages = [(p.page_num, p.text) for p in pdf_result.pages if not p.is_empty]
            chunks = chunk_document(pages)
            
            if not chunks:
                job_manager.update_stage(
                    IngestStage.CHUNKED,
                    IngestStatus.COMPLETED,
                    "No text content"
                )
                job_manager.complete_job()
                
                return ImportPdfResult(
                    success=True,
                    doc_id=doc_id,
                    job_id=job_manager.job_id,
                    pdf_key=pdf_key,
                    n_pages=pdf_result.total_pages,
                    n_chunks=0,
                    embedded_chunks=0,
                    empty_pages=pdf_result.empty_pages,
                    resumed_from=resumed_from,
                    message="No text content extracted from PDF",
                ).model_dump()
            
            # 写入 chunks 表
            with get_db() as conn:
                with conn.cursor() as cur:
                    for chunk in chunks:
                        cur.execute(
                            """
                            INSERT INTO chunks (doc_id, chunk_index, page_start, page_end, text, token_count)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING chunk_id
                            """,
                            (
                                doc_id,
                                chunk["chunk_index"],
                                chunk["page_start"],
                                chunk["page_end"],
                                chunk["text"],
                                chunk["token_count"],
                            )
                        )
                        result = cur.fetchone()
                        if result:
                            chunk_ids.append(result["chunk_id"])
            
            job_manager.update_stage(
                IngestStage.CHUNKED,
                IngestStatus.COMPLETED,
                f"Created {len(chunks)} chunks"
            )
        else:
            # 已有 chunks，获取现有数据
            existing_chunks = query_all(
                "SELECT chunk_id, text FROM chunks WHERE doc_id = %s ORDER BY chunk_index",
                (doc_id,)
            )
            chunk_ids = [c["chunk_id"] for c in existing_chunks]
            chunks = [{"text": c["text"]} for c in existing_chunks]
        
        # ==================== STAGE 5: EMBEDDED ====================
        embedded_count = 0
        
        if IngestStage.EMBEDDED.value not in completed_stages:
            job_manager.update_stage(IngestStage.EMBEDDED, IngestStatus.RUNNING)
            
            # 检查哪些 chunks 缺少 embedding
            missing = query_all(
                """
                SELECT c.chunk_id, c.text
                FROM chunks c
                LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                WHERE c.doc_id = %s AND ce.chunk_id IS NULL
                ORDER BY c.chunk_index
                """,
                (doc_id,)
            )
            
            if missing:
                missing_ids = [m["chunk_id"] for m in missing]
                missing_texts = [m["text"] for m in missing]
                
                # 生成 embeddings
                embeddings = await aget_embeddings_chunked(missing_texts)
                
                # 写入 chunk_embeddings 表
                with get_db() as conn:
                    with conn.cursor() as cur:
                        for chunk_id, embedding in zip(missing_ids, embeddings):
                            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                            cur.execute(
                                """
                                INSERT INTO chunk_embeddings (chunk_id, embedding_model, embedding)
                                VALUES (%s, %s, %s::vector)
                                ON CONFLICT (chunk_id) DO UPDATE SET
                                    embedding_model = EXCLUDED.embedding_model,
                                    embedding = EXCLUDED.embedding
                                """,
                                (chunk_id, settings.embedding_model, embedding_str)
                            )
                            embedded_count += 1
            
            # 获取总 embedding 数
            total_embedded = query_one(
                """
                SELECT COUNT(*) as count
                FROM chunk_embeddings ce
                JOIN chunks c ON ce.chunk_id = c.chunk_id
                WHERE c.doc_id = %s
                """,
                (doc_id,)
            )
            embedded_count = total_embedded["count"] if total_embedded else embedded_count
            
            job_manager.update_stage(
                IngestStage.EMBEDDED,
                IngestStatus.COMPLETED,
                f"Generated {embedded_count} embeddings"
            )
        else:
            # 获取现有 embedding 数
            total_embedded = query_one(
                """
                SELECT COUNT(*) as count
                FROM chunk_embeddings ce
                JOIN chunks c ON ce.chunk_id = c.chunk_id
                WHERE c.doc_id = %s
                """,
                (doc_id,)
            )
            embedded_count = total_embedded["count"] if total_embedded else 0
        
        # ==================== STAGE 6: COMMITTED ====================
        job_manager.update_stage(
            IngestStage.COMMITTED,
            IngestStatus.COMPLETED,
            "Import completed"
        )
        job_manager.complete_job()
        
        return ImportPdfResult(
            success=True,
            doc_id=doc_id,
            job_id=job_manager.job_id,
            pdf_key=pdf_key,
            n_pages=pdf_result.total_pages if pdf_result else 0,
            n_chunks=len(chunks) if chunks else len(chunk_ids),
            embedded_chunks=embedded_count,
            empty_pages=pdf_result.empty_pages if pdf_result else 0,
            resumed_from=resumed_from,
            message="Import completed successfully" + (f" (resumed from {resumed_from})" if resumed_from else ""),
        ).model_dump()
        
    except Exception as e:
        error_msg = str(e)
        if job_manager and job_manager.job_id:
            job_manager.fail_job(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "doc_id": doc_id,
            "job_id": job_manager.job_id if job_manager else None,
            "pdf_key": pdf_key,
            "n_pages": 0,
            "n_chunks": 0,
            "embedded_chunks": 0,
            "empty_pages": 0,
        }

def register_import_tools(mcp: FastMCP) -> None:
    """注册 PDF 导入工具"""

    @mcp.tool()
    async def import_pdf(
        file_path: str,
        title: str | None = None,
        authors: str | None = None,
        year: int | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """导入 PDF 文献到知识库"""
        return await import_pdf_run(
            file_path=file_path,
            title=title,
            authors=authors,
            year=year,
            force=force,
        )

    @mcp.tool()
    def ingest_status(
        doc_id: str | None = None,
        job_id: int | None = None,
    ) -> dict[str, Any]:
        """查看导入状态
        
        查看指定文档或作业的导入状态，包括各阶段进度和错误信息。
        
        Args:
            doc_id: 文档 ID（通过 doc_id 查询最新作业）
            job_id: 作业 ID（直接查询特定作业）
            
        Returns:
            导入状态信息，包含各阶段状态、错误摘要和建议修复动作
        """
        try:
            if not doc_id and not job_id:
                return {
                    "error": "Must provide either doc_id or job_id",
                }
            
            # 获取作业信息
            if job_id:
                job = query_one(
                    """
                    SELECT job_id, doc_id, status, current_stage, 
                           started_at::text, finished_at::text, error
                    FROM ingest_jobs
                    WHERE job_id = %s
                    """,
                    (job_id,)
                )
            else:
                job = query_one(
                    """
                    SELECT job_id, doc_id, status, current_stage,
                           started_at::text, finished_at::text, error
                    FROM ingest_jobs
                    WHERE doc_id = %s
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (doc_id,)
                )
            
            if not job:
                return {
                    "error": f"No ingest job found for {'job_id=' + str(job_id) if job_id else 'doc_id=' + doc_id}",
                    "doc_id": doc_id,
                    "job_id": job_id,
                }
            
            # 获取各阶段详情
            stages = query_all(
                """
                SELECT stage, status, message, created_at::text
                FROM ingest_job_items
                WHERE job_id = %s
                ORDER BY created_at
                """,
                (job["job_id"],)
            )
            
            # 构建阶段状态映射
            stage_status = {}
            for stage in IngestStage:
                stage_status[stage.value] = {
                    "status": "pending",
                    "message": None,
                    "timestamp": None,
                }
            
            for item in stages:
                stage_status[item["stage"]] = {
                    "status": item["status"],
                    "message": item["message"],
                    "timestamp": item["created_at"],
                }
            
            # 生成建议修复动作
            suggested_action = None
            if job["status"] == IngestStatus.FAILED.value:
                if job["current_stage"] == IngestStage.EMBEDDED.value or \
                   stage_status[IngestStage.EMBEDDED.value]["status"] == IngestStatus.FAILED.value:
                    suggested_action = f"Use reembed_document(doc_id='{job['doc_id']}') to retry embedding generation"
                elif job["current_stage"] == IngestStage.CHUNKED.value:
                    suggested_action = f"Use rechunk_document(doc_id='{job['doc_id']}', force=True) to retry chunking"
                else:
                    suggested_action = f"Use import_pdf(file_path=..., force=True) to reimport from scratch"
            elif job["status"] == IngestStatus.RUNNING.value:
                suggested_action = "Job is still running. Wait for completion or check for stuck process."
            
            # 检查文档的实际状态
            doc_stats = None
            if job["doc_id"]:
                stats = query_one(
                    """
                    SELECT 
                        (SELECT COUNT(*) FROM chunks WHERE doc_id = %s) as chunk_count,
                        (SELECT COUNT(*) FROM chunk_embeddings ce 
                         JOIN chunks c ON ce.chunk_id = c.chunk_id 
                         WHERE c.doc_id = %s) as embedded_count
                    """,
                    (job["doc_id"], job["doc_id"])
                )
                if stats:
                    doc_stats = {
                        "chunk_count": stats["chunk_count"],
                        "embedded_count": stats["embedded_count"],
                        "missing_embeddings": stats["chunk_count"] - stats["embedded_count"],
                    }
                    
                    if doc_stats["missing_embeddings"] > 0 and job["status"] == IngestStatus.COMPLETED.value:
                        suggested_action = f"Use reembed_document(doc_id='{job['doc_id']}') to fill missing embeddings"
            
            return {
                "job_id": job["job_id"],
                "doc_id": job["doc_id"],
                "status": job["status"],
                "current_stage": job["current_stage"],
                "started_at": job["started_at"],
                "finished_at": job["finished_at"],
                "error": job["error"],
                "stages": stage_status,
                "document_stats": doc_stats,
                "suggested_action": suggested_action,
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "doc_id": doc_id,
                "job_id": job_id,
            }
