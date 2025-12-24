#!/usr/bin/env python3
"""测试完整的6阶段进度报告"""

import asyncio
import os
import sys
import logging

# 设置日志输出到 stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # 简洁格式
    stream=sys.stdout,
    force=True,  # 强制覆盖任何现有配置
)

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

from paperlib_mcp.tools.import_pdf import import_pdf_run


async def main():
    print("=" * 60)
    print("🧪 测试完整6阶段进度报告 (force=True)")
    print("=" * 60)
    print()
    
    # 用最小的文件测试
    test_file = "/Users/wangxq/Documents/paperlib_mcp/test_papers/nber_33363_ai_finance_scholarship.pdf"
    
    print(f"📄 导入: {os.path.basename(test_file)}")
    print("-" * 60)
    
    # 使用 force=True 强制重新导入
    result = await import_pdf_run(test_file, force=True)
    
    print("-" * 60)
    print(f"Result: {'✅ Success' if result.get('success') else '❌ Failed'}")
    print(f"  chunks: {result.get('n_chunks', 0)}")
    print(f"  embedded: {result.get('embedded_chunks', 0)}")
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
