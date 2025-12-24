"""PDF 文本提取 - 使用 PyMuPDF4LLM"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf  # PyMuPDF (fitz)
import pymupdf4llm


@dataclass
class PdfMetadata:
    """PDF 元数据"""
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None


@dataclass
class PageText:
    """单页文本"""
    page_num: int  # 从 1 开始
    text: str
    is_empty: bool
    tables: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)


@dataclass
class PdfExtractResult:
    """PDF 提取结果"""
    total_pages: int
    pages: list[PageText]
    empty_pages: int
    metadata: PdfMetadata = field(default_factory=PdfMetadata)
    
    @property
    def all_text(self) -> str:
        """获取所有页面的合并文本"""
        return "\n\n".join(
            f"[Page {p.page_num}]\n{p.text}" 
            for p in self.pages 
            if not p.is_empty
        )
    
    @property
    def all_markdown(self) -> str:
        """获取所有页面的 Markdown 文本"""
        return "\n\n---\n\n".join(
            p.text for p in self.pages if not p.is_empty
        )


def _parse_year_from_date(date_str: str | None) -> int | None:
    """从 PDF 日期字符串中解析年份
    
    PDF 日期格式通常为: D:YYYYMMDDHHmmSSOHH'mm'
    例如: D:20231215143022+08'00'
    """
    if not date_str:
        return None
    
    # 尝试匹配 D:YYYY 或直接 YYYY 开头的格式
    match = re.search(r'D?:?(\d{4})', date_str)
    if match:
        year = int(match.group(1))
        # 合理的年份范围检查
        if 1900 <= year <= 2100:
            return year
    return None


def _clean_metadata_string(value: str | None) -> str | None:
    """清理元数据字符串，去除空白和无效值"""
    if not value:
        return None
    cleaned = value.strip()
    # 过滤掉明显无效的值
    if not cleaned or cleaned.lower() in ('unknown', 'none', 'null', ''):
        return None
    return cleaned


def extract_pdf_metadata(file_path: str | Path) -> PdfMetadata:
    """从 PDF 文件提取元数据
    
    使用 PyMuPDF 读取 PDF 的 Document Info Dictionary。
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        PdfMetadata 包含标题、作者、年份等信息
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    metadata = PdfMetadata()
    
    try:
        doc = pymupdf.open(str(file_path))
        info = doc.metadata
        
        if info:
            # 提取标题
            metadata.title = _clean_metadata_string(info.get("title"))
            
            # 提取作者
            metadata.authors = _clean_metadata_string(info.get("author"))
            
            # 提取年份 - 优先使用 creationDate，其次 modDate
            year = _parse_year_from_date(info.get("creationDate"))
            if not year:
                year = _parse_year_from_date(info.get("modDate"))
            metadata.year = year
            
            # 其他元数据
            metadata.subject = _clean_metadata_string(info.get("subject"))
            metadata.keywords = _clean_metadata_string(info.get("keywords"))
            metadata.creator = _clean_metadata_string(info.get("creator"))
            metadata.producer = _clean_metadata_string(info.get("producer"))
        
        doc.close()
    except Exception:
        # 元数据提取失败不应该阻断主流程
        pass
    
    return metadata


def extract_pdf(
    file_path: str | Path,
    *,
    table_strategy: str = "lines_strict",
    ignore_images: bool = True,
    show_progress: bool = False,
) -> PdfExtractResult:
    """从 PDF 文件提取文本（使用 PyMuPDF4LLM）
    
    PyMuPDF4LLM 优势：
    - 输出 LLM 优化的 Markdown 格式
    - 智能表格检测和格式化
    - 保留文档结构（标题、列表等）
    - 更好的多栏布局处理
    
    Args:
        file_path: PDF 文件路径
        table_strategy: 表格检测策略
            - "lines_strict": 仅检测有可见线条的表格（推荐）
            - "lines": 检测有线条的表格（更宽松）
            - "text": 基于文本对齐检测表格
            - "explicit": 仅检测明确标记的表格
        ignore_images: 是否忽略图像（默认 True，加快处理速度）
        show_progress: 是否显示进度条
        
    Returns:
        PdfExtractResult 包含所有页面的 Markdown 文本
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {file_path}")
    
    # 使用 page_chunks=True 获取每页的独立结果
    page_data = pymupdf4llm.to_markdown(
        str(file_path),
        page_chunks=True,
        table_strategy=table_strategy,
        ignore_images=ignore_images,
        show_progress=show_progress,
    )
    
    pages = []
    empty_count = 0
    
    for chunk in page_data:
        chunk_metadata = chunk.get("metadata", {})
        page_num = chunk_metadata.get("page", 0) + 1  # 转换为从 1 开始
        text = chunk.get("text", "").strip()
        tables = chunk.get("tables", [])
        images = chunk.get("images", [])
        
        is_empty = len(text) < 10  # 少于 10 个字符视为空页
        if is_empty:
            empty_count += 1
        
        pages.append(PageText(
            page_num=page_num,
            text=text,
            is_empty=is_empty,
            tables=tables,
            images=images,
        ))
    
    # 提取 PDF 元数据
    pdf_metadata = extract_pdf_metadata(file_path)
    
    return PdfExtractResult(
        total_pages=len(page_data),
        pages=pages,
        empty_pages=empty_count,
        metadata=pdf_metadata,
    )


def extract_pdf_pages(file_path: str | Path) -> list[tuple[int, str]]:
    """从 PDF 文件提取文本（简化版本）
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        列表，每项为 (page_num, text) 元组，page_num 从 1 开始
    """
    result = extract_pdf(file_path)
    return [
        (p.page_num, p.text) 
        for p in result.pages 
        if not p.is_empty
    ]


def extract_pdf_to_markdown(
    file_path: str | Path,
    *,
    pages: list[int] | None = None,
    write_images: bool = False,
    image_path: str | None = None,
    dpi: int = 150,
) -> str:
    """将 PDF 转换为单个 Markdown 字符串
    
    Args:
        file_path: PDF 文件路径
        pages: 要处理的页面列表（从 0 开始），None 表示全部
        write_images: 是否保存图像文件
        image_path: 图像保存路径
        dpi: 图像分辨率
        
    Returns:
        Markdown 格式的文本
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    kwargs: dict[str, Any] = {
        "table_strategy": "lines_strict",
    }
    
    if pages is not None:
        kwargs["pages"] = pages
    
    if write_images:
        kwargs["write_images"] = True
        kwargs["dpi"] = dpi
        if image_path:
            kwargs["image_path"] = image_path
    
    return pymupdf4llm.to_markdown(str(file_path), **kwargs)
