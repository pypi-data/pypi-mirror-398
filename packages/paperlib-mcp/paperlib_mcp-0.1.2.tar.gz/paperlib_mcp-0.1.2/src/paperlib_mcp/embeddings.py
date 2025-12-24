"""OpenRouter Embeddings API 封装"""

from typing import Any

import httpx

from paperlib_mcp.settings import get_settings


def get_embedding(text: str) -> list[float]:
    """获取单个文本的 embedding 向量
    
    Args:
        text: 输入文本
        
    Returns:
        embedding 向量（1536 维）
    """
    embeddings = get_embeddings_batch([text])
    return embeddings[0]


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """批量获取文本的 embedding 向量
    
    Args:
        texts: 输入文本列表
        
    Returns:
        embedding 向量列表
    """
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    
    url = f"{settings.openrouter_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.embedding_model,
        "input": texts,
    }
    
    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
    data = response.json()
    
    if "data" not in data:
        raise ValueError(f"OpenRouter API response missing 'data' field: {data}")

    # OpenRouter 返回的 embedding 按 index 排序
    # 确保按原始顺序返回
    embeddings_data = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in embeddings_data]

import asyncio


async def aget_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """批量获取文本的 embedding 向量 (Async)"""
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    
    url = f"{settings.openrouter_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.embedding_model,
        "input": texts,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
    data = response.json()

    if "data" not in data:
        raise ValueError(f"OpenRouter API response missing 'data' field: {data}")
    
    # OpenRouter 返回的 embedding 按 index 排序
    # 确保按原始顺序返回
    embeddings_data = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in embeddings_data]


async def aget_embeddings_chunked(
    texts: list[str], 
    batch_size: int | None = None,
    concurrency: int = 5
) -> list[list[float]]:
    """分批并行获取大量文本的 embedding 向量 (Async)
    
    Args:
        texts: 输入文本列表
        batch_size: 每批大小，默认使用配置中的值
        concurrency: 并发请求数，默认 5
    """
    settings = get_settings()
    actual_batch_size = batch_size or settings.embedding_batch_size
    
    if not texts:
        return []
    
    # 准备批次
    batches = []
    for i in range(0, len(texts), actual_batch_size):
        batches.append(texts[i:i + actual_batch_size])
    
    # 并发执行
    sem = asyncio.Semaphore(concurrency)
    results = [None] * len(batches)
    
    async def process_batch(idx, batch_texts):
        async with sem:
            embeddings = await aget_embeddings_batch(batch_texts)
            results[idx] = embeddings
    
    tasks = [process_batch(idx, b) for idx, b in enumerate(batches)]
    await asyncio.gather(*tasks)
    
    # 展平结果
    all_embeddings = []
    for batch_embeddings in results:
        if batch_embeddings:
            all_embeddings.extend(batch_embeddings)
            
    return all_embeddings


def get_embeddings_chunked(texts: list[str], batch_size: int | None = None) -> list[list[float]]:
    """分批获取大量文本的 embedding 向量 (Synchronous Wrapper)"""
    # 为了保持兼容性，这里仍然使用同步分批调用，或者可以使用 async_to_sync
    # 但原来的实现是同步的，所以保持原样即可，不需要包装 async
    settings = get_settings()
    batch_size = batch_size or settings.embedding_batch_size
    
    if not texts:
        return []
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = get_embeddings_batch(batch)
        all_embeddings.extend(batch_embeddings)
    
    return all_embeddings


def check_embeddings_api() -> dict[str, Any]:
    """检查 Embeddings API 是否可用
    
    Returns:
        API 状态信息
    """
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        return {
            "available": False,
            "error": "OPENROUTER_API_KEY is not configured",
            "model": settings.embedding_model,
        }
    
    try:
        # 使用一个简单的测试文本
        test_embedding = get_embedding("test")
        return {
            "available": True,
            "model": settings.embedding_model,
            "dimension": len(test_embedding),
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "model": settings.embedding_model,
        }
