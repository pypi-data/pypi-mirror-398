"""Paper Library MCP 服务器入口"""

from fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP(
    "Paper Library MCP",
    instructions="文献管理与检索 MCP 服务器 - 支持 PDF 导入、混合检索、文献综述生成、GraphRAG 知识图谱",
)

# 注册所有工具
from paperlib_mcp.tools.health import register_health_tools
from paperlib_mcp.tools.import_pdf import register_import_tools
from paperlib_mcp.tools.search import register_search_tools
from paperlib_mcp.tools.fetch import register_fetch_tools
from paperlib_mcp.tools.writing import register_writing_tools

# M2 GraphRAG 工具
from paperlib_mcp.tools.graph_extract import register_graph_extract_tools
from paperlib_mcp.tools.graph_canonicalize import register_graph_canonicalize_tools
from paperlib_mcp.tools.graph_community import register_graph_community_tools
from paperlib_mcp.tools.graph_summarize import register_graph_summarize_tools
from paperlib_mcp.tools.graph_maintenance import register_graph_maintenance_tools

# M3 Review 工具
from paperlib_mcp.tools.review import register_review_tools

# M4 Canonicalization & Grouping 工具
from paperlib_mcp.tools.graph_relation_canonicalize import register_graph_relation_canonicalize_tools
from paperlib_mcp.tools.graph_claim_grouping import register_graph_claim_grouping_tools
from paperlib_mcp.tools.graph_v12 import register_graph_v12_tools

register_health_tools(mcp)
register_import_tools(mcp)
register_search_tools(mcp)
register_fetch_tools(mcp)
register_writing_tools(mcp)

# 注册 M2 GraphRAG 工具
register_graph_extract_tools(mcp)
register_graph_canonicalize_tools(mcp)
register_graph_community_tools(mcp)
register_graph_summarize_tools(mcp)
register_graph_maintenance_tools(mcp)

# 注册 M3 Review 工具
register_review_tools(mcp)

# 注册 M4 Canonicalization & Grouping 工具
register_graph_relation_canonicalize_tools(mcp)
register_graph_claim_grouping_tools(mcp)
register_graph_v12_tools(mcp)


def main():
    """主入口函数"""
    mcp.run()


if __name__ == "__main__":
    main()
