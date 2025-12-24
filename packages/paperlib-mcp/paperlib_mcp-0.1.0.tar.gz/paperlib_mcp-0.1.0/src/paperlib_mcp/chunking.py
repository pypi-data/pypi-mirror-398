"""文本分块逻辑 - 按页分块"""

from dataclasses import dataclass

from paperlib_mcp.pdf_extract import PdfExtractResult


def sanitize_text(text: str) -> str:
    """Remove null bytes and other problematic characters from text.
    
    Null bytes (\x00) cause PostgreSQL JSON parsing to fail with:
    "unsupported Unicode escape sequence \\u0000 cannot be converted to text"
    """
    if not text:
        return text
    # Remove null bytes which break PostgreSQL/JSON
    return text.replace('\x00', '')


@dataclass
class Chunk:
    """文本块"""
    chunk_index: int  # 从 0 开始
    page_start: int   # 起始页码（从 1 开始）
    page_end: int     # 结束页码（从 1 开始）
    text: str
    char_count: int
    
    @property
    def estimated_tokens(self) -> int:
        """估算 token 数（约 4 字符 = 1 token）"""
        return self.char_count // 4


def chunk_pages(pages: list[tuple[int, str]]) -> list[Chunk]:
    """按页分块 - 每页一个 chunk
    
    Args:
        pages: 页面列表，每项为 (page_num, text)
        
    Returns:
        Chunk 列表，每页一个
    """
    chunks = []
    
    for chunk_index, (page_num, text) in enumerate(pages):
        if not text.strip():
            continue
        
        # Sanitize text to remove null bytes and other problematic chars
        clean_text = sanitize_text(text)
            
        chunks.append(Chunk(
            chunk_index=chunk_index,
            page_start=page_num,
            page_end=page_num,
            text=clean_text,
            char_count=len(clean_text),
        ))
    
    return chunks


def chunk_document(pages: list[tuple[int, str]]) -> list[dict]:
    """对文档按页分块（返回字典格式，便于数据库存储）
    
    Args:
        pages: 页面列表，每项为 (page_num, text)
        
    Returns:
        chunk 字典列表，包含 chunk_index, page_start, page_end, text, token_count
    """
    chunks = chunk_pages(pages)
    return [
        {
            "chunk_index": c.chunk_index,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "text": c.text,
            "token_count": c.estimated_tokens,
        }
        for c in chunks
    ]


def chunk_from_extract_result(result: PdfExtractResult) -> list[dict]:
    """从 PdfExtractResult 直接生成 chunks
    
    Args:
        result: PDF 提取结果
        
    Returns:
        chunk 字典列表
    """
    pages = [(p.page_num, p.text) for p in result.pages if not p.is_empty]
    return chunk_document(pages)
