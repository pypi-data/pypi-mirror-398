"""混合检索工具"""

from collections import defaultdict
from typing import Any
import asyncio

from pydantic import BaseModel, Field

from fastmcp import FastMCP

from paperlib_mcp.db import query_all
from paperlib_mcp.embeddings import get_embedding, aget_embeddings_batch


class SearchResult(BaseModel):
    """搜索结果"""
    chunk_id: int
    doc_id: str
    page_start: int
    page_end: int
    snippet: str
    score_total: float
    score_vec: float | None = None
    score_fts: float | None = None


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    k: int
    alpha: float
    per_doc_limit: int | None
    results: list[SearchResult]
    fts_candidates: int
    vec_candidates: int


class ExplainSearchResponse(BaseModel):
    """详细搜索解释响应"""
    query: str
    k: int
    alpha: float
    per_doc_limit: int | None
    fts_topn: int
    vec_topn: int
    final_results: list[SearchResult]
    fts_only_hits: list[SearchResult]
    vec_only_hits: list[SearchResult]
    intersection_hits: list[SearchResult]
    stats: dict[str, Any]


def search_fts(query: str, limit: int = 50) -> list[dict[str, Any]]:
    """全文搜索
    
    Args:
        query: 搜索查询
        limit: 返回结果数量
        
    Returns:
        搜索结果列表，包含 chunk_id, doc_id, page_start, page_end, text, rank
    """
    sql = """
    SELECT 
        c.chunk_id,
        c.doc_id,
        c.page_start,
        c.page_end,
        c.text,
        ts_rank(c.tsv, websearch_to_tsquery('english', %s)) as rank
    FROM chunks c
    WHERE c.tsv @@ websearch_to_tsquery('english', %s)
    ORDER BY rank DESC
    LIMIT %s
    """
    return query_all(sql, (query, query, limit))


def search_vector(query_embedding: list[float], limit: int = 50) -> list[dict[str, Any]]:
    """向量搜索
    
    Args:
        query_embedding: 查询向量
        limit: 返回结果数量
        
    Returns:
        搜索结果列表，包含 chunk_id, doc_id, page_start, page_end, text, distance
    """
    # 将 embedding 转换为 pgvector 格式
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    sql = """
    SELECT 
        c.chunk_id,
        c.doc_id,
        c.page_start,
        c.page_end,
        c.text,
        ce.embedding <=> %s::vector as distance
    FROM chunks c
    JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
    ORDER BY distance ASC
    LIMIT %s
    """
    return query_all(sql, (embedding_str, limit))


def apply_per_doc_limit(
    results: list[SearchResult],
    per_doc_limit: int | None,
) -> list[SearchResult]:
    """应用每文档限制
    
    Args:
        results: 已按 score_total 排序的结果列表
        per_doc_limit: 每篇文档最多返回的 chunk 数量
        
    Returns:
        应用限制后的结果列表
    """
    if per_doc_limit is None or per_doc_limit <= 0:
        return results
    
    doc_counts: dict[str, int] = defaultdict(int)
    filtered_results = []
    
    for result in results:
        if doc_counts[result.doc_id] < per_doc_limit:
            filtered_results.append(result)
            doc_counts[result.doc_id] += 1
    
    return filtered_results


async def hybrid_search(
    query: str,
    k: int = 10,
    alpha: float = 0.6,
    fts_topn: int = 50,
    vec_topn: int = 50,
    per_doc_limit: int | None = None,
) -> SearchResponse:
    """混合搜索（FTS + 向量）- 异步并行版
    
    Args:
        query: 搜索查询
        k: 返回结果数量
        alpha: 向量权重（FTS 权重 = 1 - alpha）
        fts_topn: FTS 候选数量
        vec_topn: 向量候选数量
        per_doc_limit: 每篇文档最多返回的 chunk 数量（None 表示不限制）
        
    Returns:
        SearchResponse 包含排序后的结果
    """
    # 并行执行：
    # 1. FTS 搜索 (DB IO)
    # 2. Embedding 生成 (Network IO)
    
    # 使用 asyncio.to_thread 运行阻塞的 DB 查询
    fts_task = asyncio.to_thread(search_fts, query, fts_topn)
    
    # 异步生成 embedding
    emb_task = aget_embeddings_batch([query])
    
    # 等待两者完成
    fts_results, embeddings = await asyncio.gather(fts_task, emb_task)
    query_embedding = embeddings[0]
    
    # 3. 向量搜索 (DB IO) - 需要等待 embedding
    vec_results = await asyncio.to_thread(search_vector, query_embedding, vec_topn)
    
    # 4. 合并结果
    # 创建 chunk_id -> 结果的映射
    all_chunks: dict[int, dict[str, Any]] = {}
    
    # 计算 FTS 归一化分数
    if fts_results:
        max_rank = max(r["rank"] for r in fts_results) or 1.0
        for r in fts_results:
            chunk_id = r["chunk_id"]
            fts_score = r["rank"] / max_rank
            all_chunks[chunk_id] = {
                "chunk_id": chunk_id,
                "doc_id": r["doc_id"],
                "page_start": r["page_start"],
                "page_end": r["page_end"],
                "text": r["text"],
                "score_fts": fts_score,
                "score_vec": None,
            }
    
    # 计算向量归一化分数
    if vec_results:
        # 距离转换为相似度：sim = 1 - distance
        # 余弦距离范围 [0, 2]，所以相似度范围 [-1, 1]
        for r in vec_results:
            chunk_id = r["chunk_id"]
            vec_score = 1.0 - r["distance"]  # 转换为相似度
            
            if chunk_id in all_chunks:
                all_chunks[chunk_id]["score_vec"] = vec_score
            else:
                all_chunks[chunk_id] = {
                    "chunk_id": chunk_id,
                    "doc_id": r["doc_id"],
                    "page_start": r["page_start"],
                    "page_end": r["page_end"],
                    "text": r["text"],
                    "score_fts": None,
                    "score_vec": vec_score,
                }
    
    # 5. 计算综合分数并排序
    results = []
    for chunk_data in all_chunks.values():
        fts_score = chunk_data["score_fts"] or 0.0
        vec_score = chunk_data["score_vec"] or 0.0
        
        # 加权平均
        total_score = alpha * vec_score + (1 - alpha) * fts_score
        
        # 生成 snippet（前 200 字符）
        text = chunk_data["text"]
        snippet = text[:200] + "..." if len(text) > 200 else text
        
        results.append(SearchResult(
            chunk_id=chunk_data["chunk_id"],
            doc_id=chunk_data["doc_id"],
            page_start=chunk_data["page_start"],
            page_end=chunk_data["page_end"],
            snippet=snippet,
            score_total=total_score,
            score_vec=chunk_data["score_vec"],
            score_fts=chunk_data["score_fts"],
        ))
    
    # 按综合分数排序
    results.sort(key=lambda x: x.score_total, reverse=True)
    
    # 应用每文档限制
    if per_doc_limit:
        results = apply_per_doc_limit(results, per_doc_limit)
    
    return SearchResponse(
        query=query,
        k=k,
        alpha=alpha,
        per_doc_limit=per_doc_limit,
        results=results[:k],
        fts_candidates=len(fts_results),
        vec_candidates=len(vec_results),
    )


async def explain_hybrid_search(
    query: str,
    k: int = 10,
    alpha: float = 0.6,
    fts_topn: int = 50,
    vec_topn: int = 50,
    per_doc_limit: int | None = None,
) -> ExplainSearchResponse:
    """详细的混合搜索（带解释）- 异步并行版"""
    
    # 并行执行 FTS 和 Embedding
    fts_task = asyncio.to_thread(search_fts, query, fts_topn)
    emb_task = aget_embeddings_batch([query])
    
    fts_results, embeddings = await asyncio.gather(fts_task, emb_task)
    query_embedding = embeddings[0]
    fts_chunk_ids = {r["chunk_id"] for r in fts_results}
    
    # 执行向量搜索
    vec_results = await asyncio.to_thread(search_vector, query_embedding, vec_topn)
    vec_chunk_ids = {r["chunk_id"] for r in vec_results}
    
    # 3. 计算交集和差集
    intersection_ids = fts_chunk_ids & vec_chunk_ids
    fts_only_ids = fts_chunk_ids - vec_chunk_ids
    vec_only_ids = vec_chunk_ids - fts_chunk_ids
    
    # 4. 合并结果
    all_chunks: dict[int, dict[str, Any]] = {}
    
    # 处理 FTS 结果
    if fts_results:
        max_rank = max(r["rank"] for r in fts_results) or 1.0
        for r in fts_results:
            chunk_id = r["chunk_id"]
            fts_score = r["rank"] / max_rank
            all_chunks[chunk_id] = {
                "chunk_id": chunk_id,
                "doc_id": r["doc_id"],
                "page_start": r["page_start"],
                "page_end": r["page_end"],
                "text": r["text"],
                "score_fts": fts_score,
                "score_vec": None,
            }
    
    # 处理向量结果
    if vec_results:
        for r in vec_results:
            chunk_id = r["chunk_id"]
            vec_score = 1.0 - r["distance"]
            
            if chunk_id in all_chunks:
                all_chunks[chunk_id]["score_vec"] = vec_score
            else:
                all_chunks[chunk_id] = {
                    "chunk_id": chunk_id,
                    "doc_id": r["doc_id"],
                    "page_start": r["page_start"],
                    "page_end": r["page_end"],
                    "text": r["text"],
                    "score_fts": None,
                    "score_vec": vec_score,
                }
    
    # 5. 创建所有结果（带综合分数）
    def make_result(chunk_data: dict[str, Any]) -> SearchResult:
        fts_score = chunk_data["score_fts"] or 0.0
        vec_score = chunk_data["score_vec"] or 0.0
        total_score = alpha * vec_score + (1 - alpha) * fts_score
        text = chunk_data["text"]
        snippet = text[:200] + "..." if len(text) > 200 else text
        
        return SearchResult(
            chunk_id=chunk_data["chunk_id"],
            doc_id=chunk_data["doc_id"],
            page_start=chunk_data["page_start"],
            page_end=chunk_data["page_end"],
            snippet=snippet,
            score_total=total_score,
            score_vec=chunk_data["score_vec"],
            score_fts=chunk_data["score_fts"],
        )
    
    # 创建各类结果列表
    all_results = [make_result(all_chunks[cid]) for cid in all_chunks]
    fts_only_hits = [make_result(all_chunks[cid]) for cid in fts_only_ids]
    vec_only_hits = [make_result(all_chunks[cid]) for cid in vec_only_ids]
    intersection_hits = [make_result(all_chunks[cid]) for cid in intersection_ids]
    
    # 排序
    all_results.sort(key=lambda x: x.score_total, reverse=True)
    fts_only_hits.sort(key=lambda x: x.score_fts or 0, reverse=True)
    vec_only_hits.sort(key=lambda x: x.score_vec or 0, reverse=True)
    intersection_hits.sort(key=lambda x: x.score_total, reverse=True)
    
    # 应用每文档限制
    final_results = apply_per_doc_limit(all_results, per_doc_limit)[:k]
    
    # 统计
    stats = {
        "total_candidates": len(all_chunks),
        "fts_candidates": len(fts_results),
        "vec_candidates": len(vec_results),
        "fts_only_count": len(fts_only_ids),
        "vec_only_count": len(vec_only_ids),
        "intersection_count": len(intersection_ids),
        "unique_docs_in_final": len(set(r.doc_id for r in final_results)),
    }
    
    return ExplainSearchResponse(
        query=query,
        k=k,
        alpha=alpha,
        per_doc_limit=per_doc_limit,
        fts_topn=fts_topn,
        vec_topn=vec_topn,
        final_results=final_results,
        fts_only_hits=fts_only_hits[:10],  # 只返回前 10 个
        vec_only_hits=vec_only_hits[:10],
        intersection_hits=intersection_hits[:10],
        stats=stats,
    )


def register_search_tools(mcp: FastMCP) -> None:
    """注册搜索工具"""

    @mcp.tool()
    async def search_hybrid(
        query: str,
        k: int = 10,
        alpha: float = 0.6,
        per_doc_limit: int = 3,
        fts_topn: int = 50,
        vec_topn: int = 50,
    ) -> dict[str, Any]:
        """混合搜索文献库
        
        使用全文搜索（FTS）和向量相似度搜索的组合，找到与查询最相关的文本块。
        
        Args:
            query: 搜索查询字符串
            k: 返回结果数量，默认 10
            alpha: 向量搜索权重（0-1），默认 0.6。FTS 权重为 1-alpha
            per_doc_limit: 每篇文档最多返回的 chunk 数量，默认 3（避免单篇论文刷屏）
            fts_topn: FTS 候选数量，默认 50
            vec_topn: 向量候选数量，默认 50
            
        Returns:
            搜索结果，包含：
            - results: 按相关性排序的 chunk 列表
            - fts_candidates: FTS 候选数量
            - vec_candidates: 向量候选数量
        """
        try:
            response = await hybrid_search(
                query, k, alpha, fts_topn, vec_topn,
                per_doc_limit=per_doc_limit if per_doc_limit > 0 else None
            )
            return response.model_dump()
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "k": k,
                "alpha": alpha,
                "results": [],
                "fts_candidates": 0,
                "vec_candidates": 0,
            }

    @mcp.tool()
    async def explain_search(
        query: str,
        k: int = 10,
        alpha: float = 0.6,
        per_doc_limit: int = 3,
        fts_topn: int = 50,
        vec_topn: int = 50,
    ) -> dict[str, Any]:
        """详细解释搜索结果
        
        执行混合搜索并返回详细的解释信息，包括 FTS-only 命中、向量-only 命中、交集命中等。
        用于调试和优化搜索参数。
        
        Args:
            query: 搜索查询字符串
            k: 返回结果数量，默认 10
            alpha: 向量搜索权重（0-1），默认 0.6
            per_doc_limit: 每篇文档最多返回的 chunk 数量，默认 3
            fts_topn: FTS 候选数量，默认 50
            vec_topn: 向量候选数量，默认 50
            
        Returns:
            详细的搜索解释，包含：
            - final_results: 最终 top-k 结果
            - fts_only_hits: 仅 FTS 命中的结果
            - vec_only_hits: 仅向量命中的结果
            - intersection_hits: 两者都命中的结果
            - stats: 统计信息
        """
        try:
            response = await explain_hybrid_search(
                query, k, alpha, fts_topn, vec_topn,
                per_doc_limit=per_doc_limit if per_doc_limit > 0 else None
            )
            return response.model_dump()
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "k": k,
                "alpha": alpha,
                "final_results": [],
                "fts_only_hits": [],
                "vec_only_hits": [],
                "intersection_hits": [],
                "stats": {},
            }

    @mcp.tool()
    def search_vector_only(
        query: str,
        k: int = 10,
    ) -> dict[str, Any]:
        """纯向量搜索
        
        仅使用向量相似度搜索，适合语义相关但关键词不匹配的场景。
        
        Args:
            query: 搜索查询字符串
            k: 返回结果数量，默认 10
            
        Returns:
            搜索结果列表
        """
        try:
            # Note: This is synchronous, but for single use it's fine. 
            # Could be asyncified if needed, but hybrid is sufficient.
            query_embedding = get_embedding(query)
            results = search_vector(query_embedding, k)
            
            formatted_results = []
            for r in results:
                text = r["text"]
                snippet = text[:200] + "..." if len(text) > 200 else text
                formatted_results.append({
                    "chunk_id": r["chunk_id"],
                    "doc_id": r["doc_id"],
                    "page_start": r["page_start"],
                    "page_end": r["page_end"],
                    "snippet": snippet,
                    "distance": r["distance"],
                    "similarity": 1.0 - r["distance"],
                })
            
            return {
                "query": query,
                "k": k,
                "results": formatted_results,
            }
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "k": k,
                "results": [],
            }

    @mcp.tool()
    def search_fts_only(
        query: str,
        k: int = 10,
    ) -> dict[str, Any]:
        """纯全文搜索
        
        仅使用 PostgreSQL 全文搜索，适合精确关键词匹配的场景。
        
        Args:
            query: 搜索查询字符串（支持布尔运算符）
            k: 返回结果数量，默认 10
            
        Returns:
            搜索结果列表
        """
        try:
            results = search_fts(query, k)
            
            formatted_results = []
            for r in results:
                text = r["text"]
                snippet = text[:200] + "..." if len(text) > 200 else text
                formatted_results.append({
                    "chunk_id": r["chunk_id"],
                    "doc_id": r["doc_id"],
                    "page_start": r["page_start"],
                    "page_end": r["page_end"],
                    "snippet": snippet,
                    "rank": r["rank"],
                })
            
            return {
                "query": query,
                "k": k,
                "results": formatted_results,
            }
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "k": k,
                "results": [],
            }
