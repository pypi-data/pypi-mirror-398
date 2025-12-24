#!/usr/bin/env python3
"""测试批量导入进度报告功能"""

import asyncio
import os
import sys

# 设置远程服务器环境变量
os.environ["POSTGRES_HOST"] = "49.234.193.192"
os.environ["POSTGRES_PORT"] = "5431"
os.environ["POSTGRES_USER"] = "paper"
os.environ["POSTGRES_PASSWORD"] = "Wshhwps#?!"
os.environ["POSTGRES_DB"] = "paperlib"
os.environ["S3_ENDPOINT"] = "http://49.234.193.192:9000"
os.environ["MINIO_ROOT_USER"] = "minio"
os.environ["MINIO_ROOT_PASSWORD"] = "Wshhwps#?!"
os.environ["OPENROUTER_API_KEY"] = "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"

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from paperlib_mcp.tools.import_pdf import batch_import_pdfs_run, import_pdf_run


async def test_single_import():
    """测试单个 PDF 导入"""
    test_dir = "/Users/wangxq/Documents/paperlib_mcp/test_papers"
    
    # 找一个 PDF 文件
    pdf_files = [f for f in os.listdir(test_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in test_papers/")
        return
    
    pdf_path = os.path.join(test_dir, pdf_files[0])
    print(f"\n📄 Testing single import: {pdf_files[0]}")
    print("=" * 60)
    
    result = await import_pdf_run(pdf_path)
    
    print(f"\nResult: {'✅ Success' if result.get('success') else '❌ Failed'}")
    if result.get("skipped"):
        print("  (Document already exists, skipped)")
    else:
        print(f"  doc_id: {result.get('doc_id', 'N/A')[:16]}...")
        print(f"  chunks: {result.get('n_chunks', 0)}")
        print(f"  embedded: {result.get('embedded_chunks', 0)}")


async def test_batch_import():
    """测试批量导入"""
    test_dir = "/Users/wangxq/Documents/paperlib_mcp/test_papers"
    
    pdf_files = [f for f in os.listdir(test_dir) if f.endswith(".pdf")]
    print(f"\n📚 Testing batch import: {len(pdf_files)} PDF files")
    print("=" * 60)
    
    result = await batch_import_pdfs_run(
        directory=test_dir,
        pattern="*.pdf",
        concurrency=3,  # 较低并发以便观察进度
    )
    
    print(f"\nFinal Result:")
    print(f"  Total: {result.get('total', 0)}")
    print(f"  Imported: {result.get('imported', 0)}")
    print(f"  Skipped: {result.get('skipped', 0)}")
    print(f"  Failed: {result.get('failed', 0)}")


async def main():
    print("=" * 60)
    print("🧪 Testing Progress Reporting for PDF Import")
    print("=" * 60)
    
    # 测试单个导入
    await test_single_import()
    
    print("\n")
    
    # 测试批量导入
    await test_batch_import()
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
