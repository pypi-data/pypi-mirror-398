#!/usr/bin/env python3
"""M3 Review Tools 扩展测试脚本

测试 M3 里程碑实现的所有 Review 工具（扩展版）：
1. generate_review_outline_data_v1 - 生成综述大纲
2. build_section_evidence_pack_v1 - 构建章节证据包
3. export_section_packet_v1 - 导出写作输入包
4. lint_section_v1 - 验证章节引用
5. compose_full_template_v1 - 生成全文模板
6. lint_review_v1 - 验证全文合规

扩展测试：
- 多章节证据包构建
- 不同大纲样式
- Lint 边界情况
- 完整写作流程模拟
"""

import sys
from pathlib import Path

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperlib_mcp.db import query_one, query_all
from paperlib_mcp.tools.review import register_review_tools
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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_subheader(title: str):
    """打印子标题"""
    print(f"\n{Colors.CYAN}--- {title} ---{Colors.RESET}")


def print_test(name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


def print_info(msg: str):
    """打印信息"""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {msg}")


class M3ExtendedTester:
    """M3 Review Tools 扩展测试器"""

    def __init__(self):
        self.mcp = FastMCP("test")
        self.passed = 0
        self.failed = 0
        self.outline_id = None
        self.section_packs = {}  # section_id -> pack_id

        # 注册工具
        register_review_tools(self.mcp)

    def call_tool(self, name: str, **kwargs):
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

    # ==================== 基础测试 ====================

    def test_generate_outline(self):
        """测试生成大纲"""
        print_header("1. 生成综述大纲 (generate_review_outline_data_v1)")

        # 使用 rebuild=True 确保新建
        result = self.call_tool(
            "generate_review_outline_data_v1",
            topic="earnings management and corporate governance",
            outline_style="econ_finance_canonical",
            rebuild=True,
        )

        self.test("返回 outline_id", result.get("outline_id") is not None)
        self.test("返回 sections", "sections" in result)
        self.test("包含 6 个章节", len(result.get("sections", [])) == 6)

        if result.get("outline_id"):
            self.outline_id = result["outline_id"]
            print_info(f"Outline ID: {self.outline_id[:8]}...")
            print_info(f"Topic: {result.get('topic')}")

        if result.get("sections"):
            section_ids = [s["section_id"] for s in result["sections"]]
            expected = ["research_question", "measurement", "identification", "findings", "debates", "gaps"]
            self.test("章节 ID 正确", section_ids == expected, str(section_ids))

    def test_outline_reproducibility(self):
        """测试大纲可复现性"""
        print_header("2. 大纲可复现性测试")

        # 同一 topic 再次生成
        result = self.call_tool(
            "generate_review_outline_data_v1",
            topic="earnings management and corporate governance",
            outline_style="econ_finance_canonical",
            rebuild=False,
        )

        self.test("返回已存在的大纲", result.get("reused", False) is True)
        self.test("outline_id 一致", result.get("outline_id") == self.outline_id)

    def test_different_outline_style(self):
        """测试不同大纲样式"""
        print_header("3. 不同大纲样式测试")

        # 使用 general 样式
        result = self.call_tool(
            "generate_review_outline_data_v1",
            topic="test topic for general style",
            outline_style="general",
            rebuild=True,
        )

        self.test("返回 outline_id", result.get("outline_id") is not None)
        self.test("使用 general 样式", result.get("outline_style") == "general")

        if result.get("sections"):
            section_ids = [s["section_id"] for s in result["sections"]]
            expected = ["background", "methodology", "findings", "discussion", "future"]
            self.test("general 样式章节正确", section_ids == expected, str(section_ids))
            print_info(f"General style sections: {len(result['sections'])}")

    # ==================== 证据包测试 ====================

    def test_build_all_section_packs(self):
        """测试构建所有章节证据包"""
        print_header("4. 构建所有章节证据包")

        if not self.outline_id:
            print_info("跳过：没有 outline_id")
            return

        sections = ["research_question", "measurement", "identification", "findings", "debates", "gaps"]

        for section_id in sections:
            print_subheader(f"Section: {section_id}")

            result = self.call_tool(
                "build_section_evidence_pack_v1",
                outline_id=self.outline_id,
                section_id=section_id,
                max_chunks=30,
                per_doc_limit=3,
                rebuild=True,
            )

            has_pack = result.get("pack_id") is not None
            self.test(f"{section_id} 返回 pack_id", has_pack)

            if has_pack:
                self.section_packs[section_id] = result["pack_id"]
                print_info(f"Pack ID: {result['pack_id']}, Chunks: {result.get('chunk_count', 0)}, Docs: {result.get('doc_count', 0)}")

    def test_pack_caching(self):
        """测试证据包缓存"""
        print_header("5. 证据包缓存测试")

        if not self.outline_id or not self.section_packs:
            print_info("跳过：没有数据")
            return

        # 选一个有数据的 section
        test_section = None
        test_pack_id = None
        for section_id, pack_id in self.section_packs.items():
            if pack_id:
                test_section = section_id
                test_pack_id = pack_id
                break

        if not test_section:
            print_info("跳过：没有有效的证据包")
            return

        # 再次请求同一 section
        result = self.call_tool(
            "build_section_evidence_pack_v1",
            outline_id=self.outline_id,
            section_id=test_section,
            rebuild=False,
        )

        self.test("复用已有 pack", result.get("reused", False) is True)
        self.test("pack_id 一致", result.get("pack_id") == test_pack_id)
        print_info(f"Section: {test_section}, Pack ID: {result.get('pack_id')}")

    # ==================== 导出测试 ====================

    def test_export_packets(self):
        """测试导出多个写作输入包"""
        print_header("6. 导出写作输入包")

        if not self.section_packs:
            print_info("跳过：没有证据包")
            return

        for section_id, pack_id in self.section_packs.items():
            if not pack_id:
                continue

            print_subheader(f"Section: {section_id}")

            result = self.call_tool("export_section_packet_v1", pack_id=pack_id)

            if "error" in result:
                print_info(f"Error: {result['error']}")
                continue

            self.test(f"{section_id} 返回 evidence", "evidence" in result)

            stats = result.get("stats", {})
            print_info(f"Chunks: {stats.get('total_chunks', 0)}, Docs: {stats.get('unique_docs', 0)}, Claims: {stats.get('total_claims', 0)}")

            # 验证 evidence 结构
            if result.get("evidence"):
                first = result["evidence"][0]
                has_anchor = "citation_anchor" in first
                self.test(f"{section_id} evidence 包含 citation_anchor", has_anchor)

    # ==================== Lint 测试 ====================

    def test_lint_valid_citations(self):
        """测试 Lint - 有效引用"""
        print_header("7. Lint Section - 有效引用")

        # 找一个有数据的 pack
        test_pack_id = None
        for pack_id in self.section_packs.values():
            if pack_id:
                test_pack_id = pack_id
                break

        if not test_pack_id:
            print_info("跳过：没有证据包")
            return

        # 获取 pack 中的所有 chunk_ids
        chunks = query_all(
            "SELECT chunk_id FROM evidence_pack_items WHERE pack_id = %s LIMIT 3",
            (test_pack_id,),
        )

        if not chunks:
            print_info("跳过：pack 为空")
            return

        # 构造有效 markdown
        citations = " ".join([f"[[chunk:{c['chunk_id']}]]" for c in chunks])
        markdown = f"""
## 测量与数据

本节讨论相关测量方法。{citations}

这是详细分析段落，引用了多个来源。
"""

        result = self.call_tool(
            "lint_section_v1",
            pack_id=test_pack_id,
            markdown=markdown,
        )

        self.test("返回 passed", "passed" in result)
        self.test("校验通过", result.get("passed", False) is True)

        stats = result.get("stats", {})
        print_info(f"Valid: {stats.get('valid_citations', 0)}, Invalid: {stats.get('invalid_citations', 0)}")

    def test_lint_invalid_chunk(self):
        """测试 Lint - 不存在的 chunk_id"""
        print_header("8. Lint Section - 不存在的 chunk_id")

        test_pack_id = None
        for pack_id in self.section_packs.values():
            if pack_id:
                test_pack_id = pack_id
                break

        if not test_pack_id:
            print_info("跳过：没有证据包")
            return

        markdown = """
## 测试

这是引用了不存在的 chunk。[[chunk:999999999]]
"""

        result = self.call_tool(
            "lint_section_v1",
            pack_id=test_pack_id,
            markdown=markdown,
        )

        self.test("校验失败", result.get("passed") is False)

        issues = result.get("issues", [])
        has_not_found = any(i["rule"] == "CHUNK_NOT_FOUND" for i in issues)
        self.test("检测到 CHUNK_NOT_FOUND", has_not_found)
        print_info(f"Issues: {len(issues)}")

    def test_lint_out_of_pack(self):
        """测试 Lint - pack 外引用"""
        print_header("9. Lint Section - Pack 外引用")

        test_pack_id = None
        for pack_id in self.section_packs.values():
            if pack_id:
                test_pack_id = pack_id
                break

        if not test_pack_id:
            print_info("跳过：没有证据包")
            return

        # 找一个存在但不在 pack 中的 chunk_id
        out_chunk = query_one(
            """
            SELECT c.chunk_id
            FROM chunks c
            WHERE c.chunk_id NOT IN (
                SELECT chunk_id FROM evidence_pack_items WHERE pack_id = %s
            )
            LIMIT 1
            """,
            (test_pack_id,),
        )

        if not out_chunk:
            print_info("跳过：无法找到 pack 外的 chunk")
            return

        out_chunk_id = out_chunk["chunk_id"]

        markdown = f"""
## 测试

这是引用了 pack 外的 chunk。[[chunk:{out_chunk_id}]]
"""

        result = self.call_tool(
            "lint_section_v1",
            pack_id=test_pack_id,
            markdown=markdown,
        )

        self.test("校验失败", result.get("passed") is False)

        issues = result.get("issues", [])
        has_out_of_pack = any(i["rule"] == "CHUNK_OUT_OF_PACK" for i in issues)
        self.test("检测到 CHUNK_OUT_OF_PACK", has_out_of_pack)
        print_info(f"Out-of-pack chunk_id: {out_chunk_id}")

    def test_lint_no_citations(self):
        """测试 Lint - 无引用"""
        print_header("10. Lint Section - 无引用")

        test_pack_id = None
        for pack_id in self.section_packs.values():
            if pack_id:
                test_pack_id = pack_id
                break

        if not test_pack_id:
            print_info("跳过：没有证据包")
            return

        markdown = """
## 测试

这是一段没有任何引用的文字。

完全没有使用证据包中的任何内容。
"""

        result = self.call_tool(
            "lint_section_v1",
            pack_id=test_pack_id,
            markdown=markdown,
        )

        # 无引用应该通过（因为 require_citations_per_paragraph 默认 False）
        self.test("无引用默认通过", result.get("passed", False) is True)

        stats = result.get("stats", {})
        self.test("total_citations = 0", stats.get("total_citations", -1) == 0)

    def test_lint_paragraph_density(self):
        """测试 Lint - 段落密度检查"""
        print_header("11. Lint Section - 段落密度检查（可选功能）")

        test_pack_id = None
        for pack_id in self.section_packs.values():
            if pack_id:
                test_pack_id = pack_id
                break

        if not test_pack_id:
            print_info("跳过：没有证据包")
            return

        markdown = """
## 测试

这是一段没有引用的文字。

另一段也没有引用。
"""

        # 开启段落密度检查
        result = self.call_tool(
            "lint_section_v1",
            pack_id=test_pack_id,
            markdown=markdown,
            require_citations_per_paragraph=True,
            min_citations_per_paragraph=1,
        )

        # 应该有 warning
        issues = result.get("issues", [])
        has_low_density = any(i["rule"] == "LOW_PARAGRAPH_DENSITY" for i in issues)
        self.test("检测到 LOW_PARAGRAPH_DENSITY", has_low_density)

        # 但仍然通过（因为是 warning 不是 error）
        self.test("仍然通过（warning不阻止）", result.get("passed", False) is True)

    # ==================== 全文测试 ====================

    def test_compose_template(self):
        """测试生成全文模板"""
        print_header("12. 生成全文模板 (compose_full_template_v1)")

        if not self.outline_id:
            print_info("跳过：没有 outline_id")
            return

        result = self.call_tool("compose_full_template_v1", outline_id=self.outline_id)

        self.test("返回 ordered_sections", "ordered_sections" in result)
        self.test("返回 template_markdown", "template_markdown" in result)

        if result.get("ordered_sections"):
            self.test("包含 6 个章节", len(result["ordered_sections"]) == 6)

        if result.get("template_markdown"):
            template = result["template_markdown"]
            self.test("模板包含占位符", "<!-- SECTION:" in template)
            self.test("模板包含参考文献", "参考文献" in template)
            print_info(f"Template length: {len(template)} chars")

    def test_lint_review_valid(self):
        """测试全文合规检查 - 有效"""
        print_header("13. 全文合规检查 - 有效引用 (lint_review_v1)")

        valid_pack_ids = [p for p in self.section_packs.values() if p]
        if not valid_pack_ids:
            print_info("跳过：没有证据包")
            return

        # 获取一些有效 chunk
        chunks = []
        for pack_id in valid_pack_ids[:2]:
            pack_chunks = query_all(
                "SELECT chunk_id FROM evidence_pack_items WHERE pack_id = %s LIMIT 2",
                (pack_id,),
            )
            chunks.extend([c["chunk_id"] for c in pack_chunks])

        if not chunks:
            print_info("跳过：没有 chunks")
            return

        citations = " ".join([f"[[chunk:{c}]]" for c in chunks])
        markdown = f"""
# 综述

## 研究问题

这是研究问题章节。{citations}

## 参考文献
"""

        result = self.call_tool(
            "lint_review_v1",
            pack_ids=valid_pack_ids,
            markdown=markdown,
        )

        self.test("返回 passed", "passed" in result)
        self.test("校验通过", result.get("passed", False) is True)

        stats = result.get("stats", {})
        print_info(f"Valid: {stats.get('valid_citations', 0)}, Coverage: {stats.get('citation_coverage_pct', 0):.1f}%")

    def test_lint_review_cross_pack(self):
        """测试全文合规检查 - 跨 pack 引用"""
        print_header("14. 全文合规检查 - 跨 Pack 引用")

        valid_pack_ids = [p for p in self.section_packs.values() if p]
        if len(valid_pack_ids) < 1:
            print_info("跳过：没有证据包")
            return

        # 只允许第一个 pack，但引用其他 pack 的 chunk
        first_pack_id = valid_pack_ids[0]

        # 找一个不在第一个 pack 的 chunk
        out_chunk = query_one(
            """
            SELECT c.chunk_id
            FROM chunks c
            WHERE c.chunk_id NOT IN (
                SELECT chunk_id FROM evidence_pack_items WHERE pack_id = %s
            )
            LIMIT 1
            """,
            (first_pack_id,),
        )

        if not out_chunk:
            print_info("跳过：无法找到外部 chunk")
            return

        markdown = f"""
# 综述

## 测试

引用了不在白名单 pack 中的 chunk。[[chunk:{out_chunk['chunk_id']}]]
"""

        result = self.call_tool(
            "lint_review_v1",
            pack_ids=[first_pack_id],  # 只允许第一个 pack
            markdown=markdown,
        )

        self.test("校验失败", result.get("passed") is False)

        issues = result.get("issues", [])
        has_out_of_pack = any(i["rule"] == "CHUNK_OUT_OF_PACK" for i in issues)
        self.test("检测到 CHUNK_OUT_OF_PACK", has_out_of_pack)

    # ==================== 完整流程模拟 ====================

    def test_full_workflow(self):
        """测试完整写作流程"""
        print_header("15. 完整写作流程模拟")

        # Step 1: 生成大纲
        print_subheader("Step 1: 生成大纲")
        outline_result = self.call_tool(
            "generate_review_outline_data_v1",
            topic="full workflow test",
            outline_style="econ_finance_canonical",
            rebuild=True,
        )
        outline_id = outline_result.get("outline_id")
        self.test("大纲生成成功", outline_id is not None)
        print_info(f"Outline ID: {outline_id[:8] if outline_id else 'N/A'}...")

        if not outline_id:
            return

        # Step 2: 为 measurement 构建证据包
        print_subheader("Step 2: 构建 measurement 证据包")
        pack_result = self.call_tool(
            "build_section_evidence_pack_v1",
            outline_id=outline_id,
            section_id="measurement",
            max_chunks=20,
        )
        pack_id = pack_result.get("pack_id")
        self.test("证据包构建成功", pack_id is not None)
        print_info(f"Pack ID: {pack_id}, Chunks: {pack_result.get('chunk_count', 0)}")

        if not pack_id:
            return

        # Step 3: 导出写作输入包
        print_subheader("Step 3: 导出写作输入包")
        packet = self.call_tool("export_section_packet_v1", pack_id=pack_id)
        evidence = packet.get("evidence", [])
        self.test("写作输入包导出成功", len(evidence) > 0)
        print_info(f"Evidence items: {len(evidence)}")

        if not evidence:
            return

        # Step 4: 模拟 Agent 写作（使用真实 chunk_id）
        print_subheader("Step 4: 模拟 Agent 写作")
        chunk_ids = [e["chunk_id"] for e in evidence[:3]]
        agent_markdown = f"""
## 测量与数据

本研究使用了多种测量方法。[[chunk:{chunk_ids[0]}]]

我们参考了以下数据来源进行分析。[[chunk:{chunk_ids[1] if len(chunk_ids) > 1 else chunk_ids[0]}]]
"""
        print_info(f"Agent 使用了 {len(chunk_ids)} 个引用")

        # Step 5: Lint 验证
        print_subheader("Step 5: Lint 验证")
        lint_result = self.call_tool(
            "lint_section_v1",
            pack_id=pack_id,
            markdown=agent_markdown,
        )
        self.test("Lint 验证通过", lint_result.get("passed", False) is True)
        print_info(f"Issues: {len(lint_result.get('issues', []))}")

        # Step 6: 生成全文模板
        print_subheader("Step 6: 生成全文模板")
        template_result = self.call_tool("compose_full_template_v1", outline_id=outline_id)
        self.test("模板生成成功", "template_markdown" in template_result)

        print_info("完整流程测试完成!")

    # ==================== 运行所有测试 ====================

    def run_all(self):
        """运行所有测试"""
        print(f"\n{Colors.BOLD}M3 Review Tools 扩展测试套件{Colors.RESET}")
        print("测试 M3 里程碑实现的所有 Review 工具（扩展版）\n")

        # 基础测试
        self.test_generate_outline()
        self.test_outline_reproducibility()
        self.test_different_outline_style()

        # 证据包测试
        self.test_build_all_section_packs()
        self.test_pack_caching()

        # 导出测试
        self.test_export_packets()

        # Lint 测试
        self.test_lint_valid_citations()
        self.test_lint_invalid_chunk()
        self.test_lint_out_of_pack()
        self.test_lint_no_citations()
        self.test_lint_paragraph_density()

        # 全文测试
        self.test_compose_template()
        self.test_lint_review_valid()
        self.test_lint_review_cross_pack()

        # 完整流程
        self.test_full_workflow()

        # 打印总结
        print_header("测试总结")
        total = self.passed + self.failed
        print(f"  总测试数: {total}")
        print(f"  {Colors.GREEN}通过: {self.passed}{Colors.RESET}")
        print(f"  {Colors.RED}失败: {self.failed}{Colors.RESET}")
        print(f"  通过率: {self.passed/total*100:.1f}%")

        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 所有测试通过！{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ 有 {self.failed} 个测试失败{Colors.RESET}")

        return self.failed == 0


def main():
    """主函数"""
    tester = M3ExtendedTester()
    success = tester.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
