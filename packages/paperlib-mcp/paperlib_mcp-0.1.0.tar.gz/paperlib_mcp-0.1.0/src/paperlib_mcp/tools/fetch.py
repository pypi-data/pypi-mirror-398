"""获取工具 - chunk 和 document 及库管理"""

from typing import Any, Literal
import tempfile
from pathlib import Path

from pydantic import BaseModel

from fastmcp import FastMCP

from paperlib_mcp.db import query_one, query_all, execute, get_db
from paperlib_mcp.storage import delete_object, get_object
from paperlib_mcp.embeddings import get_embeddings_chunked
from paperlib_mcp.pdf_extract import extract_pdf
from paperlib_mcp.chunking import chunk_document
from paperlib_mcp.settings import get_settings


class ChunkDetail(BaseModel):
    """Chunk 详细信息"""
    chunk_id: int
    doc_id: str
    chunk_index: int
    section: str | None
    page_start: int
    page_end: int
    text: str
    token_count: int | None
    has_embedding: bool


class DocumentDetail(BaseModel):
    """文档详细信息"""
    doc_id: str
    title: str | None
    authors: str | None
    year: int | None
    venue: str | None
    doi: str | None
    url: str | None
    pdf_bucket: str
    pdf_key: str
    pdf_sha256: str | None
    created_at: str | None
    updated_at: str | None
    # 统计信息
    chunk_count: int
    embedded_chunk_count: int
    total_tokens: int


def register_fetch_tools(mcp: FastMCP) -> None:
    """注册获取工具"""

    @mcp.tool()
    def get_chunk(chunk_id: int) -> dict[str, Any]:
        """获取指定 chunk 的完整内容
        
        根据 chunk_id 获取文本块的完整信息，包括全文、页码、所属文档等。
        
        Args:
            chunk_id: chunk 的唯一标识符
            
        Returns:
            chunk 的详细信息，包含：
            - chunk_id: chunk ID
            - doc_id: 所属文档 ID
            - text: 完整文本
            - page_start/page_end: 页码范围
            - has_embedding: 是否有 embedding
        """
        try:
            # 查询 chunk 信息
            chunk = query_one(
                """
                SELECT 
                    c.chunk_id,
                    c.doc_id,
                    c.chunk_index,
                    c.section,
                    c.page_start,
                    c.page_end,
                    c.text,
                    c.token_count,
                    CASE WHEN ce.chunk_id IS NOT NULL THEN true ELSE false END as has_embedding
                FROM chunks c
                LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                WHERE c.chunk_id = %s
                """,
                (chunk_id,)
            )
            
            if not chunk:
                return {
                    "error": f"Chunk not found: {chunk_id}",
                    "chunk_id": chunk_id,
                }
            
            return ChunkDetail(
                chunk_id=chunk["chunk_id"],
                doc_id=chunk["doc_id"],
                chunk_index=chunk["chunk_index"],
                section=chunk["section"],
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                text=chunk["text"],
                token_count=chunk["token_count"],
                has_embedding=chunk["has_embedding"],
            ).model_dump()
            
        except Exception as e:
            return {
                "error": str(e),
                "chunk_id": chunk_id,
            }

    @mcp.tool()
    def get_document(doc_id: str) -> dict[str, Any]:
        """获取指定文档的元数据和统计信息
        
        根据 doc_id 获取文档的完整元数据，包括标题、作者、chunk 数量等。
        
        Args:
            doc_id: 文档的唯一标识符（SHA256 哈希）
            
        Returns:
            文档的详细信息，包含：
            - 元数据：title, authors, year, venue, doi, url
            - 存储信息：pdf_bucket, pdf_key
            - 统计：chunk_count, embedded_chunk_count, total_tokens
        """
        try:
            # 查询文档基本信息
            doc = query_one(
                """
                SELECT 
                    doc_id, title, authors, year, venue, doi, url,
                    pdf_bucket, pdf_key, pdf_sha256,
                    created_at::text, updated_at::text
                FROM documents
                WHERE doc_id = %s
                """,
                (doc_id,)
            )
            
            if not doc:
                return {
                    "error": f"Document not found: {doc_id}",
                    "doc_id": doc_id,
                }
            
            # 查询统计信息
            stats = query_one(
                """
                SELECT 
                    COUNT(c.chunk_id) as chunk_count,
                    COUNT(ce.chunk_id) as embedded_chunk_count,
                    COALESCE(SUM(c.token_count), 0) as total_tokens
                FROM chunks c
                LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                WHERE c.doc_id = %s
                """,
                (doc_id,)
            )
            
            return DocumentDetail(
                doc_id=doc["doc_id"],
                title=doc["title"],
                authors=doc["authors"],
                year=doc["year"],
                venue=doc["venue"],
                doi=doc["doi"],
                url=doc["url"],
                pdf_bucket=doc["pdf_bucket"],
                pdf_key=doc["pdf_key"],
                pdf_sha256=doc["pdf_sha256"],
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
                chunk_count=stats["chunk_count"] if stats else 0,
                embedded_chunk_count=stats["embedded_chunk_count"] if stats else 0,
                total_tokens=stats["total_tokens"] if stats else 0,
            ).model_dump()
            
        except Exception as e:
            return {
                "error": str(e),
                "doc_id": doc_id,
            }

    @mcp.tool()
    def get_document_chunks(doc_id: str) -> dict[str, Any]:
        """获取指定文档的所有 chunks 列表
        
        根据 doc_id 获取该文档的所有文本块摘要信息。
        
        Args:
            doc_id: 文档的唯一标识符
            
        Returns:
            chunks 列表，每个包含 chunk_id、页码和文本摘要
        """
        try:
            chunks = query_all(
                """
                SELECT 
                    c.chunk_id,
                    c.chunk_index,
                    c.page_start,
                    c.page_end,
                    c.token_count,
                    LEFT(c.text, 100) as snippet,
                    CASE WHEN ce.chunk_id IS NOT NULL THEN true ELSE false END as has_embedding
                FROM chunks c
                LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                WHERE c.doc_id = %s
                ORDER BY c.chunk_index
                """,
                (doc_id,)
            )
            
            return {
                "doc_id": doc_id,
                "chunk_count": len(chunks),
                "chunks": [
                    {
                        "chunk_id": c["chunk_id"],
                        "chunk_index": c["chunk_index"],
                        "page_start": c["page_start"],
                        "page_end": c["page_end"],
                        "token_count": c["token_count"],
                        "snippet": c["snippet"] + "..." if len(c["snippet"]) >= 100 else c["snippet"],
                        "has_embedding": c["has_embedding"],
                    }
                    for c in chunks
                ],
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "doc_id": doc_id,
                "chunks": [],
            }

    @mcp.tool()
    def list_documents(
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        has_embeddings: bool | None = None,
    ) -> dict[str, Any]:
        """列出所有已导入的文档
        
        获取文献库中所有文档的摘要列表，支持排序和筛选。
        
        Args:
            limit: 返回结果数量限制，默认 50
            offset: 分页偏移量，默认 0
            order_by: 排序字段，可选 "created_at"（默认）、"year"、"title"
            has_embeddings: 筛选条件，True=只显示有完整embedding的，False=只显示缺embedding的，None=显示全部
            
        Returns:
            文档列表，包含基本信息和 chunk/embedding 统计
        """
        try:
            # 验证 order_by 参数
            valid_order_by = {"created_at": "d.created_at", "year": "d.year", "title": "d.title"}
            order_column = valid_order_by.get(order_by, "d.created_at")
            
            # 构建基础查询
            base_query = """
                SELECT 
                    d.doc_id,
                    d.title,
                    d.authors,
                    d.year,
                    d.created_at::text,
                    COUNT(c.chunk_id) as chunk_count,
                    COUNT(ce.chunk_id) as embedded_count
                FROM documents d
                LEFT JOIN chunks c ON d.doc_id = c.doc_id
                LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                GROUP BY d.doc_id
            """
            
            # 添加筛选条件
            if has_embeddings is True:
                # 只显示所有 chunk 都有 embedding 的文档
                base_query += " HAVING COUNT(c.chunk_id) > 0 AND COUNT(c.chunk_id) = COUNT(ce.chunk_id)"
            elif has_embeddings is False:
                # 只显示缺少 embedding 的文档
                base_query += " HAVING COUNT(c.chunk_id) > COUNT(ce.chunk_id)"
            
            # 添加排序（处理 NULL 值）
            if order_by == "year":
                base_query += f" ORDER BY {order_column} DESC NULLS LAST"
            elif order_by == "title":
                base_query += f" ORDER BY {order_column} ASC NULLS LAST"
            else:
                base_query += f" ORDER BY {order_column} DESC"
            
            # 添加分页
            base_query += " LIMIT %s OFFSET %s"
            
            docs = query_all(base_query, (limit, offset))
            
            # 获取总数（考虑筛选条件）
            if has_embeddings is True:
                total_query = """
                    SELECT COUNT(*) as count FROM (
                        SELECT d.doc_id
                        FROM documents d
                        LEFT JOIN chunks c ON d.doc_id = c.doc_id
                        LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                        GROUP BY d.doc_id
                        HAVING COUNT(c.chunk_id) > 0 AND COUNT(c.chunk_id) = COUNT(ce.chunk_id)
                    ) sub
                """
            elif has_embeddings is False:
                total_query = """
                    SELECT COUNT(*) as count FROM (
                        SELECT d.doc_id
                        FROM documents d
                        LEFT JOIN chunks c ON d.doc_id = c.doc_id
                        LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                        GROUP BY d.doc_id
                        HAVING COUNT(c.chunk_id) > COUNT(ce.chunk_id)
                    ) sub
                """
            else:
                total_query = "SELECT COUNT(*) as count FROM documents"
            
            total = query_one(total_query)
            
            return {
                "total": total["count"] if total else 0,
                "limit": limit,
                "offset": offset,
                "order_by": order_by,
                "has_embeddings_filter": has_embeddings,
                "documents": [
                    {
                        "doc_id": d["doc_id"],
                        "title": d["title"],
                        "authors": d["authors"],
                        "year": d["year"],
                        "created_at": d["created_at"],
                        "chunk_count": d["chunk_count"],
                        "embedded_count": d["embedded_count"],
                        "fully_embedded": d["chunk_count"] > 0 and d["chunk_count"] == d["embedded_count"],
                    }
                    for d in docs
                ],
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total": 0,
                "documents": [],
            }

    @mcp.tool()
    def delete_document(
        doc_id: str,
        also_delete_object: bool = False,
    ) -> dict[str, Any]:
        """删除指定文档
        
        从数据库删除文档及其所有关联数据（chunks、embeddings、导入记录等）。
        可选择同时删除 MinIO 中的 PDF 文件。
        
        Args:
            doc_id: 文档的唯一标识符
            also_delete_object: 是否同时删除 MinIO 中的 PDF 文件，默认 False
            
        Returns:
            删除结果，包含删除的记录数量
        """
        try:
            # 先获取文档信息
            doc = query_one(
                "SELECT pdf_key FROM documents WHERE doc_id = %s",
                (doc_id,)
            )
            
            if not doc:
                return {
                    "success": False,
                    "error": f"Document not found: {doc_id}",
                    "doc_id": doc_id,
                }
            
            pdf_key = doc["pdf_key"]
            
            # 统计将要删除的数据
            stats = query_one(
                """
                SELECT 
                    (SELECT COUNT(*) FROM chunks WHERE doc_id = %s) as chunk_count,
                    (SELECT COUNT(*) FROM chunk_embeddings ce 
                     JOIN chunks c ON ce.chunk_id = c.chunk_id 
                     WHERE c.doc_id = %s) as embedding_count,
                    (SELECT COUNT(*) FROM ingest_jobs WHERE doc_id = %s) as job_count
                """,
                (doc_id, doc_id, doc_id)
            )
            
            # 删除导入记录
            execute("DELETE FROM ingest_jobs WHERE doc_id = %s", (doc_id,))
            
            # 删除文档（级联删除 chunks 和 embeddings）
            execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
            
            result = {
                "success": True,
                "doc_id": doc_id,
                "deleted_chunks": stats["chunk_count"] if stats else 0,
                "deleted_embeddings": stats["embedding_count"] if stats else 0,
                "deleted_jobs": stats["job_count"] if stats else 0,
                "object_deleted": False,
            }
            
            # 可选删除 MinIO 对象
            if also_delete_object and pdf_key:
                delete_result = delete_object(pdf_key)
                result["object_deleted"] = delete_result.get("deleted", False)
                result["pdf_key"] = pdf_key
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "doc_id": doc_id,
            }

    @mcp.tool()
    def update_document(
        doc_id: str,
        title: str | None = None,
        authors: str | None = None,
        year: int | None = None,
        venue: str | None = None,
        doi: str | None = None,
        url: str | None = None,
    ) -> dict[str, Any]:
        """更新指定文档的元数据
        
        根据 doc_id 更新文档的元数据信息。只有提供的字段会被更新，
        未提供的字段保持原值不变。
        
        Args:
            doc_id: 文档的唯一标识符（SHA256 哈希）
            title: 新的论文标题
            authors: 新的作者列表
            year: 新的发表年份
            venue: 新的期刊/会议名称
            doi: 新的 DOI 标识符
            url: 新的论文链接
            
        Returns:
            更新结果，包含：
            - success: 是否成功
            - doc_id: 文档 ID
            - updated_fields: 更新的字段列表
            - document: 更新后的文档信息
        """
        try:
            # 检查文档是否存在
            existing = query_one(
                "SELECT doc_id FROM documents WHERE doc_id = %s",
                (doc_id,)
            )
            
            if not existing:
                return {
                    "success": False,
                    "error": f"Document not found: {doc_id}",
                    "doc_id": doc_id,
                }
            
            # 收集要更新的字段
            update_fields = []
            update_values = []
            updated_field_names = []
            
            if title is not None:
                update_fields.append("title = %s")
                update_values.append(title)
                updated_field_names.append("title")
            
            if authors is not None:
                update_fields.append("authors = %s")
                update_values.append(authors)
                updated_field_names.append("authors")
            
            if year is not None:
                update_fields.append("year = %s")
                update_values.append(year)
                updated_field_names.append("year")
            
            if venue is not None:
                update_fields.append("venue = %s")
                update_values.append(venue)
                updated_field_names.append("venue")
            
            if doi is not None:
                update_fields.append("doi = %s")
                update_values.append(doi)
                updated_field_names.append("doi")
            
            if url is not None:
                update_fields.append("url = %s")
                update_values.append(url)
                updated_field_names.append("url")
            
            if not update_fields:
                return {
                    "success": False,
                    "error": "No fields to update. Please provide at least one field.",
                    "doc_id": doc_id,
                }
            
            # 添加 updated_at
            update_fields.append("updated_at = now()")
            
            # 构建并执行 UPDATE 语句
            update_sql = f"""
                UPDATE documents
                SET {', '.join(update_fields)}
                WHERE doc_id = %s
                RETURNING 
                    doc_id, title, authors, year, venue, doi, url,
                    pdf_bucket, pdf_key, pdf_sha256,
                    created_at::text, updated_at::text
            """
            update_values.append(doc_id)
            
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(update_sql, tuple(update_values))
                    updated_doc = cur.fetchone()
            
            if not updated_doc:
                return {
                    "success": False,
                    "error": f"Failed to update document: {doc_id}",
                    "doc_id": doc_id,
                }
            
            return {
                "success": True,
                "doc_id": doc_id,
                "updated_fields": updated_field_names,
                "document": {
                    "doc_id": updated_doc["doc_id"],
                    "title": updated_doc["title"],
                    "authors": updated_doc["authors"],
                    "year": updated_doc["year"],
                    "venue": updated_doc["venue"],
                    "doi": updated_doc["doi"],
                    "url": updated_doc["url"],
                    "pdf_bucket": updated_doc["pdf_bucket"],
                    "pdf_key": updated_doc["pdf_key"],
                    "pdf_sha256": updated_doc["pdf_sha256"],
                    "created_at": updated_doc["created_at"],
                    "updated_at": updated_doc["updated_at"],
                },
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "doc_id": doc_id,
            }

    @mcp.tool()
    def reembed_document(
        doc_id: str,
        batch_size: int = 64,
        force: bool = False,
    ) -> dict[str, Any]:
        """重新生成文档的 embedding
        
        为文档的 chunks 生成 embedding。默认只处理缺失 embedding 的 chunks，
        设置 force=True 可重新生成所有 embedding。
        
        Args:
            doc_id: 文档的唯一标识符
            batch_size: 批处理大小，默认 64
            force: 是否强制重新生成所有 embedding，默认 False
            
        Returns:
            处理结果，包含处理的 chunk 数量
        """
        try:
            # 检查文档是否存在
            doc = query_one(
                "SELECT doc_id FROM documents WHERE doc_id = %s",
                (doc_id,)
            )
            
            if not doc:
                return {
                    "success": False,
                    "error": f"Document not found: {doc_id}",
                    "doc_id": doc_id,
                }
            
            settings = get_settings()
            
            # 查找需要处理的 chunks
            if force:
                # 删除现有 embeddings
                execute(
                    """
                    DELETE FROM chunk_embeddings 
                    WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE doc_id = %s)
                    """,
                    (doc_id,)
                )
                chunks = query_all(
                    "SELECT chunk_id, text FROM chunks WHERE doc_id = %s ORDER BY chunk_index",
                    (doc_id,)
                )
            else:
                # 只查找缺失 embedding 的 chunks
                chunks = query_all(
                    """
                    SELECT c.chunk_id, c.text 
                    FROM chunks c
                    LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                    WHERE c.doc_id = %s AND ce.chunk_id IS NULL
                    ORDER BY c.chunk_index
                    """,
                    (doc_id,)
                )
            
            if not chunks:
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "processed_chunks": 0,
                    "message": "No chunks need embedding",
                }
            
            # 批量生成 embeddings
            chunk_ids = [c["chunk_id"] for c in chunks]
            texts = [c["text"] for c in chunks]
            embeddings = get_embeddings_chunked(texts, batch_size=batch_size)
            
            # 写入数据库
            embedded_count = 0
            with get_db() as conn:
                with conn.cursor() as cur:
                    for chunk_id, embedding in zip(chunk_ids, embeddings):
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
            
            return {
                "success": True,
                "doc_id": doc_id,
                "processed_chunks": embedded_count,
                "total_chunks": len(chunks),
                "embedding_model": settings.embedding_model,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "doc_id": doc_id,
            }

    @mcp.tool()
    def rechunk_document(
        doc_id: str,
        strategy: str = "page_v1",
        force: bool = False,
    ) -> dict[str, Any]:
        """重新分块文档
        
        从 MinIO 获取 PDF，重新提取文本并分块，然后生成新的 embeddings。
        会删除旧的 chunks 和 embeddings。
        
        Args:
            doc_id: 文档的唯一标识符
            strategy: 分块策略，目前支持 "page_v1"（按页分块）
            force: 是否强制执行（即使已有 chunks），默认 False
            
        Returns:
            处理结果，包含新的 chunk 数量
        """
        try:
            # 检查文档是否存在
            doc = query_one(
                "SELECT doc_id, pdf_key FROM documents WHERE doc_id = %s",
                (doc_id,)
            )
            
            if not doc:
                return {
                    "success": False,
                    "error": f"Document not found: {doc_id}",
                    "doc_id": doc_id,
                }
            
            # 检查是否已有 chunks
            existing = query_one(
                "SELECT COUNT(*) as count FROM chunks WHERE doc_id = %s",
                (doc_id,)
            )
            
            if existing and existing["count"] > 0 and not force:
                return {
                    "success": False,
                    "error": f"Document already has {existing['count']} chunks. Use force=True to rechunk.",
                    "doc_id": doc_id,
                    "existing_chunks": existing["count"],
                }
            
            settings = get_settings()
            
            # 从 MinIO 获取 PDF
            pdf_content = get_object(doc["pdf_key"])
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_content)
                tmp_path = tmp.name
            
            try:
                # 提取文本
                pdf_result = extract_pdf(tmp_path)
                
                # 删除旧的 chunks（级联删除 embeddings）
                execute("DELETE FROM chunks WHERE doc_id = %s", (doc_id,))
                
                # 分块
                pages = [(p.page_num, p.text) for p in pdf_result.pages if not p.is_empty]
                chunks = chunk_document(pages)
                
                if not chunks:
                    return {
                        "success": True,
                        "doc_id": doc_id,
                        "n_chunks": 0,
                        "message": "No text content extracted from PDF",
                    }
                
                # 写入 chunks 表
                chunk_ids = []
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
                
                # 生成 embeddings
                texts = [c["text"] for c in chunks]
                embeddings = get_embeddings_chunked(texts)
                
                # 写入 embeddings
                embedded_count = 0
                with get_db() as conn:
                    with conn.cursor() as cur:
                        for chunk_id, embedding in zip(chunk_ids, embeddings):
                            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                            cur.execute(
                                """
                                INSERT INTO chunk_embeddings (chunk_id, embedding_model, embedding)
                                VALUES (%s, %s, %s::vector)
                                """,
                                (chunk_id, settings.embedding_model, embedding_str)
                            )
                            embedded_count += 1
                
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "strategy": strategy,
                    "n_pages": pdf_result.total_pages,
                    "n_chunks": len(chunks),
                    "embedded_chunks": embedded_count,
                }
                
            finally:
                # 清理临时文件
                Path(tmp_path).unlink(missing_ok=True)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "doc_id": doc_id,
            }
