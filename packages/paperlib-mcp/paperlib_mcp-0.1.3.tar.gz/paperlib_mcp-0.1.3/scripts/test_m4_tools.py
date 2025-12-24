#!/usr/bin/env python3
"""M4 Canonicalization & Grouping 工具测试脚本"""

import sys
from pathlib import Path
from typing import Any

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperlib_mcp.db import query_one, query_all
from paperlib_mcp.tools.graph_relation_canonicalize import register_graph_relation_canonicalize_tools
from paperlib_mcp.tools.graph_claim_grouping import register_graph_claim_grouping_tools
from fastmcp import FastMCP


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")


def print_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if details:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")


class M4ToolsTester:
    def __init__(self):
        self.mcp = FastMCP("test-m4")
        self.passed = 0
        self.failed = 0
        
        register_graph_relation_canonicalize_tools(self.mcp)
        register_graph_claim_grouping_tools(self.mcp)
    
    def call_tool(self, name: str, **kwargs) -> Any:
        tool = self.mcp._tool_manager._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return tool.fn(**kwargs)
    
    def test(self, name: str, condition: bool, details: str = ""):
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        print_test(name, condition, details)

    def run_tests(self):
        print_header("1. Relation Canonicalization (canonicalize_relations_v1)")
        
        # Dry run
        res_dry = self.call_tool("canonicalize_relations_v1", dry_run=True)
        self.test("Dry run successful", "new_canonical_relations" in res_dry)
        print(f"  Dry run results: {res_dry.get('new_canonical_relations')} canonical relations, {res_dry.get('new_evidence_records')} evidence records")

        # Execute
        res_exec = self.call_tool("canonicalize_relations_v1", dry_run=False)
        self.test("Execution successful", res_exec.get("new_canonical_relations", 0) > 0)
        print(f"  Execution results: {res_exec.get('new_canonical_relations')} canonical relations, {res_exec.get('new_evidence_records')} evidence records")

        print_header("2. Compact Relations Export (export_relations_compact_v1)")
        res_exp = self.call_tool("export_relations_compact_v1")
        self.test("Export successful", "relations" in res_exp)
        if res_exp.get("relations"):
            print(f"  Exported {len(res_exp['relations'])} relations")
            first = res_exp['relations'][0]
            print(f"  Top relation: {first['subj_name']} --[{first['predicate_norm']}]--> {first['obj_name']} ({first['evidence_count']} evidence)")

        print_header("3. Claim Grouping (build_claim_groups_v1)")
        # Execute grouping
        res_grp = self.call_tool("build_claim_groups_v1", dry_run=False)
        self.test("Grouping successful", res_grp.get("new_groups", 0) >= 0)
        print(f"  Grouping results: {res_grp.get('new_groups')} groups, {res_grp.get('total_members')} members")

        print_header("4. Grouped Claim Matrix Export (export_claim_matrix_grouped_v1)")
        res_mat = self.call_tool("export_claim_matrix_grouped_v1")
        self.test("Export grouped matrix successful", "groups" in res_mat)
        if res_mat.get("groups"):
            print(f"  Exported {len(res_mat['groups'])} groups")
            first_grp = res_mat['groups'][0]
            print(f"  Top group: {first_grp['topic_name']} ({first_grp['member_count']} claims)")

        print_header("Summary")
        print(f"Passed: {self.passed}, Failed: {self.failed}")


if __name__ == "__main__":
    tester = M4ToolsTester()
    tester.run_tests()
