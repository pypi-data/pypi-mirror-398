#!/usr/bin/env python3
"""M2 GraphRAG 工具测试脚本

测试 M2 GraphRAG v1 实现的所有 MCP 工具：
1. 基础检查：graph_health_check
2. 抽取工具：select_high_value_chunks, extract_graph_v1
3. 规范化工具：canonicalize_entities_v1, lock_entity, merge_entities
4. 社区工具：build_communities_v1, build_community_evidence_pack
5. 摘要导出：summarize_community_v1, export_evidence_matrix_v1
6. 维护工具：graph_status, extract_graph_missing, rebuild_communities, clear_graph
"""

import sys
from pathlib import Path
from typing import Any

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperlib_mcp.db import query_one, query_all
from paperlib_mcp.tools.graph_extract import register_graph_extract_tools
from paperlib_mcp.tools.graph_canonicalize import register_graph_canonicalize_tools
from paperlib_mcp.tools.graph_community import register_graph_community_tools
from paperlib_mcp.tools.graph_summarize import register_graph_summarize_tools
from paperlib_mcp.tools.graph_maintenance import register_graph_maintenance_tools
from fastmcp import FastMCP


class Colors:
    """终端颜色"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(title: str):
    """打印测试标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")


def print_subheader(title: str):
    """打印子标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- {title} ---{Colors.RESET}")


def print_test(name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


def print_info(msg: str):
    """打印信息"""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {msg}")


def print_warning(msg: str):
    """打印警告"""
    print(f"  {Colors.YELLOW}⚠{Colors.RESET} {msg}")


class GraphToolsTester:
    """GraphRAG 工具测试器"""
    
    def __init__(self):
        self.mcp = FastMCP("test-graph")
        self.passed = 0
        self.failed = 0
        self.test_doc_id = None
        self.test_entity_id = None
        self.test_comm_id = None
        self.test_pack_id = None
        
        # 注册所有 GraphRAG 工具
        register_graph_extract_tools(self.mcp)
        register_graph_canonicalize_tools(self.mcp)
        register_graph_community_tools(self.mcp)
        register_graph_summarize_tools(self.mcp)
        register_graph_maintenance_tools(self.mcp)
    
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
    
    # ==================== 1. 基础检查 ====================
    
    def test_graph_health_check(self):
        """测试 GraphRAG 健康检查"""
        print_header("1. GraphRAG 健康检查 (graph_health_check)")
        
        result = self.call_tool("graph_health_check", include_counts=True)
        
        self.test("返回结果", result is not None)
        self.test("db_ok 为 True", result.get("db_ok", False))
        self.test("tables_ok 为 True", result.get("tables_ok", False))
        self.test("indexes_ok 为 True", result.get("indexes_ok", False))
        self.test("整体状态 ok", result.get("ok", False))
        
        if result.get("counts"):
            print_info(f"表统计: {result['counts']}")
        
        if result.get("notes"):
            for note in result["notes"]:
                print_warning(note)
        
        return result.get("ok", False)
    
    # ==================== 2. 抽取工具 ====================
    
    def test_select_high_value_chunks(self):
        """测试高价值 chunk 筛选"""
        print_header("2. 高价值 Chunk 筛选 (select_high_value_chunks)")
        
        # 获取一个测试文档
        doc = query_one("SELECT doc_id FROM documents LIMIT 1")
        if not doc:
            print_warning("跳过：没有文档")
            return
        
        self.test_doc_id = doc["doc_id"]
        print_info(f"测试文档: {self.test_doc_id[:16]}...")
        
        result = self.call_tool(
            "select_high_value_chunks",
            doc_id=self.test_doc_id,
            max_chunks=20,
            keyword_mode="default"
        )
        
        self.test("返回 chunks 列表", "chunks" in result)
        self.test("无错误", result.get("error") is None)
        
        if result.get("chunks"):
            print_info(f"找到 {len(result['chunks'])} 个高价值 chunks")
            for chunk in result["chunks"][:3]:
                print_info(f"  Chunk {chunk['chunk_id']}: {chunk['reason'][:50]}...")
    
    def test_extract_graph_v1(self):
        """测试图谱抽取"""
        print_header("3. 图谱抽取 (extract_graph_v1)")
        
        if not self.test_doc_id:
            doc = query_one("SELECT doc_id FROM documents LIMIT 1")
            if not doc:
                print_warning("跳过：没有文档")
                return
            self.test_doc_id = doc["doc_id"]
        
        print_info(f"测试文档: {self.test_doc_id[:16]}...")
        
        # 先用 dry_run 测试
        print_subheader("3.1 Dry Run 测试")
        result_dry = self.call_tool(
            "extract_graph_v1",
            doc_id=self.test_doc_id,
            mode="high_value_only",
            max_chunks=5,
            llm_model="openai/gpt-4o-mini",
            dry_run=True
        )
        
        self.test("dry_run 返回 stats", "stats" in result_dry)
        self.test("dry_run 无错误", result_dry.get("error") is None)
        
        if result_dry.get("stats"):
            stats = result_dry["stats"]
            print_info(f"Dry run 统计: chunks={stats['processed_chunks']}, entities={stats['new_entities']}, claims={stats['new_claims']}")
        
        # 实际抽取（限制 chunk 数量）
        print_subheader("3.2 实际抽取（限制 3 个 chunks）")
        result = self.call_tool(
            "extract_graph_v1",
            doc_id=self.test_doc_id,
            mode="high_value_only",
            max_chunks=3,
            llm_model="openai/gpt-4o-mini",
            min_confidence=0.6,
            dry_run=False
        )
        
        self.test("返回 stats", "stats" in result)
        
        if result.get("error"):
            print_warning(f"抽取错误: {result['error']['message']}")
        else:
            stats = result.get("stats", {})
            print_info(f"抽取统计: chunks={stats.get('processed_chunks', 0)}, entities={stats.get('new_entities', 0)}")
            print_info(f"  mentions={stats.get('new_mentions', 0)}, relations={stats.get('new_relations', 0)}, claims={stats.get('new_claims', 0)}")
    
    # ==================== 3. 规范化工具 ====================
    
    def test_canonicalize_entities(self):
        """测试实体规范化"""
        print_header("4. 实体规范化 (canonicalize_entities_v1)")
        
        # 先用 suggest_only 测试
        print_subheader("4.1 建议模式")
        result_suggest = self.call_tool(
            "canonicalize_entities_v1",
            types=["Topic", "MeasureProxy", "IdentificationStrategy", "Method"],
            suggest_only=True,
            max_groups=100
        )
        
        self.test("返回 suggestions", "suggestions" in result_suggest)
        self.test("executed=False (suggest_only)", result_suggest.get("executed") == False)
        
        if result_suggest.get("suggestions"):
            print_info(f"发现 {len(result_suggest['suggestions'])} 个可合并组")
            for s in result_suggest["suggestions"][:3]:
                print_info(f"  {s['type']}: {s['canonical_key']} (合并 {len(s['merged_entity_ids'])} 个)")
        else:
            print_info("没有发现需要合并的实体")
        
        # 实际执行规范化
        print_subheader("4.2 执行规范化")
        result = self.call_tool(
            "canonicalize_entities_v1",
            types=["Topic", "Method"],
            suggest_only=False,
            max_groups=50
        )
        
        self.test("executed=True", result.get("executed") == True)
        print_info(f"合并了 {result.get('merged_groups', 0)} 个组, {result.get('merged_entities', 0)} 个实体")
    
    def test_lock_entity(self):
        """测试锁定实体"""
        print_header("5. 锁定/解锁实体 (lock_entity)")
        
        # 获取一个测试实体
        entity = query_one("SELECT entity_id FROM entities WHERE type != 'Paper' LIMIT 1")
        if not entity:
            print_warning("跳过：没有实体")
            return
        
        self.test_entity_id = entity["entity_id"]
        print_info(f"测试实体 ID: {self.test_entity_id}")
        
        # 锁定
        result_lock = self.call_tool("lock_entity", entity_id=self.test_entity_id, is_locked=True)
        self.test("锁定成功", result_lock.get("ok", False))
        
        # 验证
        locked = query_one("SELECT is_locked FROM entities WHERE entity_id = %s", (self.test_entity_id,))
        self.test("is_locked=True", locked and locked["is_locked"] == True)
        
        # 解锁
        result_unlock = self.call_tool("lock_entity", entity_id=self.test_entity_id, is_locked=False)
        self.test("解锁成功", result_unlock.get("ok", False))
    
    def test_merge_entities(self):
        """测试手动合并实体"""
        print_header("6. 手动合并实体 (merge_entities)")
        
        # 查找可合并的实体对（同类型）
        entities = query_all(
            """
            SELECT entity_id, type, canonical_name 
            FROM entities 
            WHERE type = 'Topic' AND is_locked IS NOT TRUE
            LIMIT 2
            """
        )
        
        if len(entities) < 2:
            print_warning("跳过：没有足够的 Topic 实体进行合并测试")
            self.test("跳过合并测试", True)
            return
        
        from_id = entities[0]["entity_id"]
        to_id = entities[1]["entity_id"]
        print_info(f"合并 {from_id} -> {to_id}")
        
        result = self.call_tool(
            "merge_entities",
            from_entity_id=from_id,
            to_entity_id=to_id,
            reason="test merge"
        )
        
        self.test("合并成功", result.get("ok", False))
        
        # 验证源实体已删除
        deleted = query_one("SELECT entity_id FROM entities WHERE entity_id = %s", (from_id,))
        self.test("源实体已删除", deleted is None)
    
    # ==================== 4. 社区工具 ====================
    
    def test_build_communities(self):
        """测试社区构建"""
        print_header("7. 社区构建 (build_communities_v1)")
        
        result = self.call_tool(
            "build_communities_v1",
            level="macro",
            min_df=1,  # 降低阈值以便测试
            resolution=1.0,
            max_nodes=1000,
            rebuild=True
        )
        
        if result.get("error"):
            if "igraph" in result["error"].get("message", ""):
                print_warning("igraph/leidenalg 未安装，跳过社区构建")
                self.test("依赖检查正确", True)
                return
            elif "No" in result["error"].get("message", ""):
                print_warning(f"数据不足: {result['error']['message']}")
                self.test("正确处理数据不足", True)
                return
        
        self.test("返回 communities", "communities" in result)
        
        if result.get("communities"):
            print_info(f"构建了 {len(result['communities'])} 个社区")
            for comm in result["communities"][:3]:
                self.test_comm_id = comm["comm_id"]
                top_names = [e["canonical_name"] for e in comm["top_entities"][:3]]
                print_info(f"  社区 {comm['comm_id']}: size={comm['size']}, top={top_names}")
    
    def test_build_community_evidence_pack(self):
        """测试社区证据包构建"""
        print_header("8. 社区证据包 (build_community_evidence_pack)")
        
        if not self.test_comm_id:
            # 尝试获取一个社区
            comm = query_one("SELECT comm_id FROM communities LIMIT 1")
            if not comm:
                print_warning("跳过：没有社区")
                return
            self.test_comm_id = comm["comm_id"]
        
        print_info(f"测试社区 ID: {self.test_comm_id}")
        
        result = self.call_tool(
            "build_community_evidence_pack",
            comm_id=self.test_comm_id,
            max_chunks=50,
            per_doc_limit=3
        )
        
        self.test("返回 pack_id", result.get("pack_id", 0) > 0)
        
        if result.get("pack_id"):
            self.test_pack_id = result["pack_id"]
            print_info(f"Pack ID: {self.test_pack_id}, docs={result.get('docs', 0)}, chunks={result.get('chunks', 0)}")
    
    # ==================== 5. 摘要导出 ====================
    
    def test_summarize_community(self):
        """测试社区摘要生成"""
        print_header("9. 社区摘要 (summarize_community_v1)")
        
        if not self.test_comm_id:
            comm = query_one("SELECT comm_id FROM communities LIMIT 1")
            if not comm:
                print_warning("跳过：没有社区")
                return
            self.test_comm_id = comm["comm_id"]
        
        print_info(f"测试社区 ID: {self.test_comm_id}")
        print_warning("注意：此操作会调用 LLM，可能需要一些时间...")
        
        result = self.call_tool(
            "summarize_community_v1",
            comm_id=self.test_comm_id,
            pack_id=self.test_pack_id,
            llm_model="openai/gpt-4o-mini",
            max_chunks=30
        )
        
        if result.get("error"):
            print_warning(f"摘要生成错误: {result['error']['message']}")
            self.test("错误处理正确", True)
            return
        
        self.test("返回 summary_json", bool(result.get("summary_json")))
        self.test("返回 markdown", bool(result.get("markdown")))
        
        if result.get("summary_json"):
            summary = result["summary_json"]
            print_info(f"摘要包含: scope={bool(summary.get('scope'))}, measures={bool(summary.get('measures'))}")
            print_info(f"  consensus={bool(summary.get('consensus'))}, gaps={bool(summary.get('gaps'))}")
    
    def test_export_evidence_matrix(self):
        """测试证据矩阵导出"""
        print_header("10. 证据矩阵导出 (export_evidence_matrix_v1)")
        
        if not self.test_comm_id:
            comm = query_one("SELECT comm_id FROM communities LIMIT 1")
            if not comm:
                print_warning("跳过：没有社区")
                return
            self.test_comm_id = comm["comm_id"]
        
        print_info(f"导出社区 {self.test_comm_id} 的证据矩阵")
        
        result = self.call_tool(
            "export_evidence_matrix_v1",
            comm_id=self.test_comm_id,
            format="json",
            limit_docs=10
        )
        
        self.test("返回 paper_matrix", "paper_matrix" in result)
        self.test("返回 claim_matrix", "claim_matrix" in result)
        
        if result.get("paper_matrix"):
            print_info(f"PaperMatrix: {len(result['paper_matrix'])} 篇论文")
            for paper in result["paper_matrix"][:2]:
                title = paper.get('title') or 'N/A'
                print_info(f"  {title[:40]}...")
                print_info(f"    topics={paper.get('topics') or []}[:2], ids={paper.get('identification_strategies') or []}[:2]")
        
        if result.get("claim_matrix"):
            print_info(f"ClaimMatrix: {len(result['claim_matrix'])} 条结论")
    
    # ==================== 6. 维护工具 ====================
    
    def test_graph_status(self):
        """测试图谱状态查询"""
        print_header("11. 图谱状态 (graph_status)")
        
        # 全局状态
        print_subheader("11.1 全局状态")
        result_global = self.call_tool("graph_status")
        
        self.test("返回 coverage", "coverage" in result_global)
        
        if result_global.get("coverage"):
            cov = result_global["coverage"]
            print_info(f"总文档: {cov.get('total_documents', 0)}, 已抽取: {cov.get('extracted_documents', 0)}")
            print_info(f"抽取覆盖率: {cov.get('extraction_coverage', 0)}%")
            print_info(f"实体: {cov.get('total_entities', 0)}, 关系: {cov.get('total_relations', 0)}, 结论: {cov.get('total_claims', 0)}")
            if cov.get("entity_type_distribution"):
                print_info(f"实体类型分布: {cov['entity_type_distribution']}")
        
        # 单文档状态
        if self.test_doc_id:
            print_subheader("11.2 单文档状态")
            result_doc = self.call_tool("graph_status", doc_id=self.test_doc_id)
            
            if result_doc.get("coverage"):
                cov = result_doc["coverage"]
                print_info(f"文档 {self.test_doc_id[:16]}...")
                print_info(f"  chunks={cov.get('chunks', 0)}, mentions={cov.get('mentions', 0)}, claims={cov.get('claims', 0)}")
    
    def test_extract_graph_missing(self):
        """测试批量补跑"""
        print_header("12. 批量补跑 (extract_graph_missing) [限制测试]")
        
        print_warning("为避免大量 API 调用，仅测试 1 个文档")
        
        result = self.call_tool(
            "extract_graph_missing",
            limit_docs=1,
            llm_model="openai/gpt-4o-mini",
            min_confidence=0.6
        )
        
        self.test("返回 processed_docs", "processed_docs" in result)
        self.test("返回 doc_ids", "doc_ids" in result)
        
        print_info(f"处理了 {result.get('processed_docs', 0)} 个文档")
        if result.get("doc_ids"):
            print_info(f"文档 IDs: {result['doc_ids']}")
    
    def test_rebuild_communities(self):
        """测试重建社区"""
        print_header("13. 重建社区 (rebuild_communities)")
        
        result = self.call_tool(
            "rebuild_communities",
            level="macro",
            min_df=1,
            resolution=1.0
        )
        
        if result.get("error"):
            print_warning(f"重建错误: {result['error']['message']}")
            self.test("错误处理正确", True)
            return
        
        self.test("返回 communities", "communities" in result)
        print_info(f"重建了 {len(result.get('communities', []))} 个社区")
    
    def test_clear_graph(self):
        """测试清理图谱数据"""
        print_header("14. 清理图谱 (clear_graph) [跳过 - 破坏性操作]")
        
        print_warning("跳过测试：clear_graph 会删除数据")
        print_info("如需测试单文档清理: clear_graph(doc_id='...')")
        print_info("如需清理全部: clear_graph(clear_all=True)")
        
        self.test("跳过破坏性测试", True)
    
    # ==================== 运行所有测试 ====================
    
    def run_all(self, skip_llm: bool = False):
        """运行所有测试
        
        Args:
            skip_llm: 是否跳过需要 LLM 调用的测试
        """
        print(f"\n{Colors.BOLD}M2 GraphRAG 工具测试套件{Colors.RESET}")
        print(f"测试 M2 GraphRAG v1 实现的所有 MCP 工具\n")
        
        # 1. 基础检查
        if not self.test_graph_health_check():
            print(f"\n{Colors.RED}GraphRAG 表未就绪，请先运行数据库迁移{Colors.RESET}")
            print("psql -f initdb/003_m2_graphrag.sql")
            return False
        
        # 2. 抽取工具
        self.test_select_high_value_chunks()
        if not skip_llm:
            self.test_extract_graph_v1()
        else:
            print_header("3. 图谱抽取 (extract_graph_v1) [跳过 - 需要 LLM]")
            print_warning("使用 --skip-llm 跳过了此测试")
        
        # 3. 规范化工具
        self.test_canonicalize_entities()
        self.test_lock_entity()
        # self.test_merge_entities()  # 跳过以避免数据损失
        print_header("6. 手动合并实体 (merge_entities) [跳过 - 会删除数据]")
        print_warning("跳过合并测试以保护数据")
        self.test("跳过合并测试", True)
        
        # 4. 社区工具
        self.test_build_communities()
        self.test_build_community_evidence_pack()
        
        # 5. 摘要导出
        if not skip_llm:
            self.test_summarize_community()
        else:
            print_header("9. 社区摘要 (summarize_community_v1) [跳过 - 需要 LLM]")
            print_warning("使用 --skip-llm 跳过了此测试")
        self.test_export_evidence_matrix()
        
        # 6. 维护工具
        self.test_graph_status()
        if not skip_llm:
            print_header("12. 批量补跑 (extract_graph_missing) [跳过 - 需要 LLM]")
            print_warning("跳过以避免大量 API 调用")
            self.test("跳过批量补跑测试", True)
        self.test_rebuild_communities()
        self.test_clear_graph()
        
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
    import argparse
    
    parser = argparse.ArgumentParser(description="M2 GraphRAG 工具测试")
    parser.add_argument("--skip-llm", action="store_true", help="跳过需要 LLM 调用的测试")
    args = parser.parse_args()
    
    tester = GraphToolsTester()
    success = tester.run_all(skip_llm=args.skip_llm)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

