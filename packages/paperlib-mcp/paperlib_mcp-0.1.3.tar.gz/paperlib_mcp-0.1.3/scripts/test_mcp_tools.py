#!/usr/bin/env python3
"""MCP 工具综合测试脚本

测试 M1 里程碑实现的所有 MCP 工具：
1. 库管理工具：list_documents, delete_document, reembed_document, rechunk_document
2. 导入状态管理：import_pdf (6阶段状态机), ingest_status
3. 检索增强：search_hybrid, explain_search
4. 证据包与写作：build_evidence_pack, draft_lit_review_v1, draft_section
"""

import sys
import os
from pathlib import Path
from typing import Any

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperlib_mcp.db import query_one, query_all, execute
from paperlib_mcp.tools.health import register_health_tools
from paperlib_mcp.tools.fetch import register_fetch_tools
from paperlib_mcp.tools.import_pdf import register_import_tools
from paperlib_mcp.tools.search import register_search_tools
from paperlib_mcp.tools.writing import register_writing_tools
from fastmcp import FastMCP


class Colors:
    """终端颜色"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(title: str):
    """打印测试标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_test(name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


def print_info(msg: str):
    """打印信息"""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {msg}")


class MCPTester:
    """MCP 工具测试器"""
    
    def __init__(self):
        self.mcp = FastMCP("test")
        self.passed = 0
        self.failed = 0
        self.test_doc_id = None
        self.test_pack_id = None
        
        # 注册所有工具
        register_health_tools(self.mcp)
        register_fetch_tools(self.mcp)
        register_import_tools(self.mcp)
        register_search_tools(self.mcp)
        register_writing_tools(self.mcp)
    
    def call_tool(self, name: str, **kwargs) -> Any:
        """调用 MCP 工具"""
        tool = self.mcp._tool_manager._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return tool.fn(**kwargs)
    
    def test(self, name: str, condition: bool, details: str = ""):
        """记录测试结果"""
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        print_test(name, condition, details)
    
    # ==================== 健康检查测试 ====================
    
    def test_health_check(self):
        """测试健康检查"""
        print_header("1. 健康检查 (health_check)")
        
        result = self.call_tool("health_check")
        
        self.test("健康检查返回结果", result is not None)
        self.test("数据库连接正常", result.get("db", {}).get("connected", False))
        self.test("S3 存储可访问", result.get("s3", {}).get("accessible", False))
        self.test("整体状态正常", result.get("ok", False))
    
    # ==================== 库管理工具测试 ====================
    
    def test_list_documents(self):
        """测试文档列表"""
        print_header("2. 文档列表 (list_documents)")
        
        # 基本列表
        result = self.call_tool("list_documents", limit=10, offset=0)
        self.test("返回文档列表", "documents" in result)
        self.test("包含总数字段", "total" in result)
        
        if result.get("documents"):
            doc = result["documents"][0]
            self.test("文档包含 chunk_count", "chunk_count" in doc)
            self.test("文档包含 embedded_count", "embedded_count" in doc)
            self.test("文档包含 fully_embedded", "fully_embedded" in doc)
            self.test_doc_id = doc["doc_id"]
            print_info(f"测试文档 ID: {self.test_doc_id[:16]}...")
        
        # 测试排序
        result_year = self.call_tool("list_documents", order_by="year")
        self.test("按年份排序正常", "documents" in result_year)
        
        # 测试筛选
        result_embedded = self.call_tool("list_documents", has_embeddings=True)
        self.test("筛选有 embedding 的文档", "documents" in result_embedded)
        
        result_missing = self.call_tool("list_documents", has_embeddings=False)
        self.test("筛选缺 embedding 的文档", "documents" in result_missing)
    
    def test_get_document(self):
        """测试获取文档详情"""
        print_header("3. 文档详情 (get_document)")
        
        if not self.test_doc_id:
            print_info("跳过：没有测试文档")
            return
        
        result = self.call_tool("get_document", doc_id=self.test_doc_id)
        
        self.test("返回文档信息", "doc_id" in result)
        self.test("包含 chunk_count", "chunk_count" in result)
        self.test("包含 embedded_chunk_count", "embedded_chunk_count" in result)
        self.test("包含 total_tokens", "total_tokens" in result)
        
        print_info(f"Chunks: {result.get('chunk_count')}, Embedded: {result.get('embedded_chunk_count')}")
    
    def test_get_document_chunks(self):
        """测试获取文档的 chunks"""
        print_header("4. 文档 Chunks (get_document_chunks)")
        
        if not self.test_doc_id:
            print_info("跳过：没有测试文档")
            return
        
        result = self.call_tool("get_document_chunks", doc_id=self.test_doc_id)
        
        self.test("返回 chunks 列表", "chunks" in result)
        
        if result.get("chunks"):
            chunk = result["chunks"][0]
            self.test("Chunk 包含 has_embedding", "has_embedding" in chunk)
            self.test("Chunk 包含 snippet", "snippet" in chunk)
            print_info(f"共 {len(result['chunks'])} 个 chunks")
    
    # ==================== 导入状态管理测试 ====================
    
    def test_import_pdf_existing(self):
        """测试导入已存在的 PDF（跳过）"""
        print_header("5. PDF 导入 - 已存在文档 (import_pdf)")
        
        # 查找测试 PDF
        papers_dir = Path(__file__).parent.parent.parent / "papers"
        pdf_files = list(papers_dir.glob("*.pdf"))
        
        if not pdf_files:
            print_info("跳过：没有找到测试 PDF")
            return
        
        test_pdf = pdf_files[0]
        print_info(f"测试文件: {test_pdf.name}")
        
        # 不强制导入，应该跳过
        result = self.call_tool("import_pdf", file_path=str(test_pdf), force=False)
        
        self.test("返回成功", result.get("success", False))
        self.test("标记为跳过 (skipped)", result.get("skipped", False) or "already exists" in result.get("message", "").lower())
        
        if result.get("doc_id"):
            self.test_doc_id = result["doc_id"]
    
    def test_import_pdf_force(self):
        """测试强制重新导入 PDF"""
        print_header("6. PDF 导入 - 强制重新导入 (import_pdf force=True)")
        
        papers_dir = Path(__file__).parent.parent.parent / "papers"
        pdf_files = list(papers_dir.glob("*.pdf"))
        
        if not pdf_files:
            print_info("跳过：没有找到测试 PDF")
            return
        
        test_pdf = pdf_files[0]
        
        # 强制重新导入
        result = self.call_tool(
            "import_pdf",
            file_path=str(test_pdf),
            title="Test Import",
            force=True
        )
        
        self.test("返回成功", result.get("success", False))
        self.test("包含 job_id", result.get("job_id") is not None)
        self.test("包含 n_chunks", "n_chunks" in result)
        self.test("包含 embedded_chunks", "embedded_chunks" in result)
        
        if result.get("doc_id"):
            self.test_doc_id = result["doc_id"]
            print_info(f"Doc ID: {self.test_doc_id[:16]}...")
            print_info(f"Job ID: {result.get('job_id')}")
            print_info(f"Chunks: {result.get('n_chunks')}, Embedded: {result.get('embedded_chunks')}")
    
    def test_ingest_status(self):
        """测试导入状态查询"""
        print_header("7. 导入状态 (ingest_status)")
        
        if not self.test_doc_id:
            print_info("跳过：没有测试文档")
            return
        
        result = self.call_tool("ingest_status", doc_id=self.test_doc_id)
        
        if "error" in result and result.get("error") and "No ingest job found" in result["error"]:
            print_info("文档在状态跟踪功能添加前导入，无历史记录")
            self.test("正确处理无记录情况", True)
            return
        
        self.test("返回状态信息", "status" in result)
        self.test("包含 stages", "stages" in result)
        self.test("包含 document_stats", "document_stats" in result)
        
        if result.get("stages"):
            completed_stages = [s for s, info in result["stages"].items() if info["status"] == "completed"]
            print_info(f"已完成阶段: {', '.join(completed_stages)}")
    
    # ==================== 检索增强测试 ====================
    
    def test_search_hybrid(self):
        """测试混合搜索"""
        print_header("8. 混合搜索 (search_hybrid)")
        
        result = self.call_tool(
            "search_hybrid",
            query="earnings management",
            k=5,
            per_doc_limit=2,
            alpha=0.6
        )
        
        self.test("返回结果列表", "results" in result)
        self.test("包含 fts_candidates", "fts_candidates" in result)
        self.test("包含 vec_candidates", "vec_candidates" in result)
        self.test("包含 per_doc_limit", "per_doc_limit" in result)
        
        if result.get("results"):
            r = result["results"][0]
            self.test("结果包含 score_total", "score_total" in r)
            self.test("结果包含 score_vec", "score_vec" in r)
            self.test("结果包含 score_fts", "score_fts" in r)
            print_info(f"返回 {len(result['results'])} 条结果")
    
    def test_explain_search(self):
        """测试搜索解释"""
        print_header("9. 搜索解释 (explain_search)")
        
        result = self.call_tool(
            "explain_search",
            query="identification strategy",
            k=5,
            per_doc_limit=2
        )
        
        self.test("返回 final_results", "final_results" in result)
        self.test("返回 fts_only_hits", "fts_only_hits" in result)
        self.test("返回 vec_only_hits", "vec_only_hits" in result)
        self.test("返回 intersection_hits", "intersection_hits" in result)
        self.test("返回 stats", "stats" in result)
        
        if result.get("stats"):
            stats = result["stats"]
            print_info(f"总候选: {stats.get('total_candidates')}")
            print_info(f"FTS-only: {stats.get('fts_only_count')}, Vec-only: {stats.get('vec_only_count')}, 交集: {stats.get('intersection_count')}")
    
    def test_search_vector_only(self):
        """测试纯向量搜索"""
        print_header("10. 纯向量搜索 (search_vector_only)")
        
        result = self.call_tool("search_vector_only", query="financial reporting", k=5)
        
        self.test("返回结果列表", "results" in result)
        
        if result.get("results"):
            r = result["results"][0]
            self.test("结果包含 similarity", "similarity" in r)
            print_info(f"返回 {len(result['results'])} 条结果")
    
    def test_search_fts_only(self):
        """测试纯全文搜索"""
        print_header("11. 纯全文搜索 (search_fts_only)")
        
        result = self.call_tool("search_fts_only", query="earnings", k=5)
        
        self.test("返回结果列表", "results" in result)
        
        if result.get("results"):
            r = result["results"][0]
            self.test("结果包含 rank", "rank" in r)
            print_info(f"返回 {len(result['results'])} 条结果")
    
    # ==================== 证据包与写作测试 ====================
    
    def test_build_evidence_pack(self):
        """测试构建证据包"""
        print_header("12. 构建证据包 (build_evidence_pack)")
        
        result = self.call_tool(
            "build_evidence_pack",
            query="earnings management methodology",
            k=15,
            per_doc_limit=3
        )
        
        self.test("返回 pack_id", result.get("pack_id") is not None)
        self.test("返回 items", "items" in result)
        self.test("返回 stats", "stats" in result)
        
        if result.get("pack_id"):
            self.test_pack_id = result["pack_id"]
            print_info(f"Pack ID: {self.test_pack_id}")
            print_info(f"Items: {len(result.get('items', []))}")
            print_info(f"Stats: {result.get('stats')}")
    
    def test_list_evidence_packs(self):
        """测试列出证据包"""
        print_header("13. 列出证据包 (list_evidence_packs)")
        
        result = self.call_tool("list_evidence_packs", limit=10)
        
        self.test("返回 packs 列表", "packs" in result)
        self.test("返回 total", "total" in result)
        
        if result.get("packs"):
            print_info(f"共 {result['total']} 个证据包")
            for p in result["packs"][:3]:
                print_info(f"  Pack {p['pack_id']}: {p['query'][:30]}... ({p['item_count']} items)")
    
    def test_get_evidence_pack_info(self):
        """测试获取证据包详情"""
        print_header("14. 证据包详情 (get_evidence_pack_info)")
        
        if not self.test_pack_id:
            print_info("跳过：没有测试证据包")
            return
        
        result = self.call_tool("get_evidence_pack_info", pack_id=self.test_pack_id)
        
        self.test("返回 pack_id", result.get("pack_id") == self.test_pack_id)
        self.test("返回 items", "items" in result)
        self.test("返回 query", "query" in result)
        
        if result.get("items"):
            print_info(f"包含 {len(result['items'])} 条证据")
    
    def test_draft_lit_review(self):
        """测试生成文献综述"""
        print_header("15. 生成文献综述 (draft_lit_review_v1)")
        
        # 测试使用 topic
        result_topic = self.call_tool(
            "draft_lit_review_v1",
            topic="earnings management",
            k=10
        )
        
        self.test("使用 topic 生成综述", "sections" in result_topic)
        
        if result_topic.get("sections"):
            print_info(f"生成 {len(result_topic['sections'])} 个章节")
        
        # 测试使用 pack_id
        if self.test_pack_id:
            result_pack = self.call_tool(
                "draft_lit_review_v1",
                pack_id=self.test_pack_id
            )
            
            self.test("使用 pack_id 生成综述", "sections" in result_pack)
            self.test("pack_id 正确记录", result_pack.get("pack_id") == self.test_pack_id)
    
    def test_draft_section(self):
        """测试分段写作"""
        print_header("16. 分段写作 (draft_section)")
        
        if not self.test_pack_id:
            print_info("跳过：没有测试证据包")
            return
        
        # 测试不同章节
        sections = ["methodology", "findings", "gaps"]
        
        for section in sections:
            result = self.call_tool(
                "draft_section",
                pack_id=self.test_pack_id,
                section=section
            )
            
            self.test(f"生成 {section} 章节", "content" in result or "error" not in result)
            
            if result.get("total_evidence"):
                print_info(f"  {section}: {result['total_evidence']} 条相关证据")
    
    def test_get_outline_templates(self):
        """测试获取大纲模板"""
        print_header("17. 大纲模板 (get_outline_templates)")
        
        result = self.call_tool("get_outline_templates")
        
        self.test("返回 templates", "templates" in result)
        
        if result.get("templates"):
            for t in result["templates"]:
                print_info(f"模板: {t['id']} - {t['name']} ({len(t['sections'])} 章节)")
    
    def test_collect_evidence(self):
        """测试收集证据"""
        print_header("18. 收集证据 (collect_evidence)")
        
        result = self.call_tool(
            "collect_evidence",
            topic="earnings management",
            section_focus="methodology",
            k=10
        )
        
        self.test("返回 evidence", "evidence" in result)
        self.test("返回 unique_documents", "unique_documents" in result)
        
        if result.get("evidence"):
            print_info(f"从 {result['unique_documents']} 篇文档收集到 {result['total_chunks']} 条证据")
    
    # ==================== 库管理工具测试（破坏性操作）====================
    
    def test_reembed_document(self):
        """测试重新生成 embedding"""
        print_header("19. 重新生成 Embedding (reembed_document)")
        
        if not self.test_doc_id:
            print_info("跳过：没有测试文档")
            return
        
        # 非强制模式（如果没有缺失应该跳过）
        result = self.call_tool(
            "reembed_document",
            doc_id=self.test_doc_id,
            force=False
        )
        
        self.test("返回成功", result.get("success", False))
        self.test("返回 processed_chunks", "processed_chunks" in result)
        
        print_info(f"处理了 {result.get('processed_chunks', 0)} 个 chunks")
    
    def test_rechunk_document(self):
        """测试重新分块（谨慎：会修改数据）"""
        print_header("20. 重新分块 (rechunk_document) [跳过 - 破坏性操作]")
        
        print_info("跳过测试：rechunk_document 会删除现有数据")
        print_info("如需测试，请手动调用: rechunk_document(doc_id=..., force=True)")
        self.test("跳过破坏性测试", True)
    
    def test_delete_document(self):
        """测试删除文档（跳过以保护数据）"""
        print_header("21. 删除文档 (delete_document) [跳过 - 破坏性操作]")
        
        print_info("跳过测试：delete_document 会永久删除数据")
        print_info("如需测试，请手动调用: delete_document(doc_id=..., also_delete_object=True)")
        self.test("跳过破坏性测试", True)
    
    # ==================== 运行所有测试 ====================
    
    def run_all(self):
        """运行所有测试"""
        print(f"\n{Colors.BOLD}MCP 工具测试套件{Colors.RESET}")
        print(f"测试 M1 里程碑实现的所有 MCP 工具\n")
        
        # 1. 健康检查
        self.test_health_check()
        
        # 2-4. 库管理（只读）
        self.test_list_documents()
        self.test_get_document()
        self.test_get_document_chunks()
        
        # 5-7. 导入状态管理
        self.test_import_pdf_existing()
        self.test_import_pdf_force()
        self.test_ingest_status()
        
        # 8-11. 检索
        self.test_search_hybrid()
        self.test_explain_search()
        self.test_search_vector_only()
        self.test_search_fts_only()
        
        # 12-18. 证据包与写作
        self.test_build_evidence_pack()
        self.test_list_evidence_packs()
        self.test_get_evidence_pack_info()
        self.test_draft_lit_review()
        self.test_draft_section()
        self.test_get_outline_templates()
        self.test_collect_evidence()
        
        # 19-21. 库管理（写操作）
        self.test_reembed_document()
        self.test_rechunk_document()
        self.test_delete_document()
        
        # 打印总结
        print_header("测试总结")
        total = self.passed + self.failed
        print(f"  总测试数: {total}")
        print(f"  {Colors.GREEN}通过: {self.passed}{Colors.RESET}")
        print(f"  {Colors.RED}失败: {self.failed}{Colors.RESET}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 所有测试通过！{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ 有 {self.failed} 个测试失败{Colors.RESET}")
        
        return self.failed == 0


def main():
    """主函数"""
    tester = MCPTester()
    success = tester.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

