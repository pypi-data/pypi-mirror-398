# Paperlib MCP

学术文献管理与检索 MCP 服务器 - 支持 PDF 导入、混合检索、知识图谱构建和文献综述生成。

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| **PDF 导入** | 自动提取文本、按页分块、生成向量嵌入 |
| **混合检索** | FTS 全文搜索 + pgvector 向量搜索 |
| **知识图谱** | LLM 驱动实体/关系/结论抽取，Leiden 社区发现 |
| **综述生成** | 基于证据包的结构化文献综述自动生成 |

## 📋 前置要求

- PostgreSQL 16+ with pgvector 扩展
- MinIO 或 S3 兼容存储
- OpenRouter API Key

---

## 🚀 安装与使用

### 方式 1: Docker Compose (推荐新手)

一键启动完整环境（PostgreSQL + MinIO + MCP）：

```bash
git clone https://github.com/your-org/paperlib-mcp.git
cd paperlib-mcp

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入 OPENROUTER_API_KEY

# 启动服务
docker-compose up -d
```

#### 在 Cursor 中配置

使用 `claude_desktop_config.json` 快速配置：

```json
{
  "mcpServers": {
    "paperlib-docker": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "paperlib-mcp",
        "python",
        "-m",
        "paperlib_mcp.server"
      ]
    }
  }
}
```


### 方式 2: uvx 安装 (推荐)

**前提**: 需要可用的 PostgreSQL（with pgvector）和 MinIO/S3 兼容存储服务。

<details>
<summary>💡 快速启动本地服务（可选）</summary>

```bash
docker-compose up -d postgres minio minio-init
```
</details>

在 Cursor/Claude Desktop 中配置，根据实际服务地址修改环境变量：

```json
{
  "mcpServers": {
    "paperlib": {
      "command": "uvx",
      "args": ["paperlib-mcp"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_USER": "paper",
        "POSTGRES_PASSWORD": "paper",
        "POSTGRES_DB": "paperlib",
        "S3_ENDPOINT": "http://localhost:9000",
        "MINIO_ROOT_USER": "minio",
        "MINIO_ROOT_PASSWORD": "minio123",
        "OPENROUTER_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 方式 3: pip 安装

**前提**: 同方式 2，需要可用的 PostgreSQL 和 MinIO/S3 服务。

```bash
pip install paperlib-mcp
```

配置 MCP 客户端（根据实际服务地址修改）：

```json
{
  "mcpServers": {
    "paperlib": {
      "command": "paperlib-mcp",
      "args": [],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_USER": "paper",
        "POSTGRES_PASSWORD": "paper",
        "POSTGRES_DB": "paperlib",
        "S3_ENDPOINT": "http://localhost:9000",
        "MINIO_ROOT_USER": "minio",
        "MINIO_ROOT_PASSWORD": "minio123",
        "OPENROUTER_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 方式 4: 本地开发

```bash
git clone https://github.com/your-org/paperlib-mcp.git
cd paperlib-mcp

uv sync
cp .env.example .env
# 编辑 .env

uv run python -m paperlib_mcp.server
```

---

## 📖 可用工具

### 基础工具
| 工具 | 说明 |
|------|------|
| `health_check` | 系统健康检查 |
| `import_pdf` | 导入 PDF 文献 |
| `search_hybrid` | 混合搜索 (推荐) |
| `get_document` | 获取文档元数据 |
| `list_documents` | 列出所有文档 |

### 图谱工具
| 工具 | 说明 |
|------|------|
| `extract_graph_v1` | 抽取知识图谱 |
| `build_communities_v1` | 构建主题社区 |
| `summarize_community_v1` | 生成社区摘要 |

### 写作工具
| 工具 | 说明 |
|------|------|
| `build_evidence_pack` | 构建证据包 |
| `draft_lit_review_v1` | 生成综述草稿 |

> 完整工具列表 (48+) 见 [docs/MCP_TOOLS_REFERENCE.md](./docs/MCP_TOOLS_REFERENCE.md)

---

## 💡 使用示例

```bash
# 导入 PDF
> import_pdf file_path="/papers/study.pdf" title="Study Title"

# 搜索文献
> search_hybrid query="monetary policy" k=10

# 构建知识图谱
> extract_graph_v1 doc_id="abc123"
> build_communities_v1 level="macro"

# 生成综述
> build_evidence_pack query="CBDC" k=40
> draft_lit_review_v1 pack_id=1
```

---

## 📚 技术文档

| 文档 | 说明 |
|------|------|
| [DEPLOYMENT.md](./docs/DEPLOYMENT.md) | 部署指南 |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构 |
| [EMBEDDING_SYSTEM.md](./docs/EMBEDDING_SYSTEM.md) | 嵌入与检索 |
| [KNOWLEDGE_GRAPH.md](./docs/KNOWLEDGE_GRAPH.md) | 知识图谱 |
| [DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md) | 数据库结构 |
| [MCP_TOOLS_REFERENCE.md](./docs/MCP_TOOLS_REFERENCE.md) | 工具 API |

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| MCP 协议 | FastMCP |
| 数据库 | PostgreSQL 16 + pgvector |
| 对象存储 | MinIO (S3 兼容) |
| PDF 处理 | PyMuPDF4LLM |
| 嵌入模型 | OpenRouter (text-embedding-3-small) |
| 图聚类 | igraph + Leiden |

---

## 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `OPENROUTER_API_KEY` | ✅ | - | OpenRouter API 密钥 |
| `POSTGRES_HOST` | ❌ | `localhost` | 数据库主机 |
| `POSTGRES_USER` | ❌ | `paper` | 数据库用户 |
| `POSTGRES_PASSWORD` | ❌ | `paper` | 数据库密码 |
| `POSTGRES_DB` | ❌ | `paperlib` | 数据库名 |
| `S3_ENDPOINT` | ❌ | `http://localhost:9000` | MinIO 端点 |
| `MINIO_ROOT_USER` | ❌ | `minio` | MinIO 用户 |
| `MINIO_ROOT_PASSWORD` | ❌ | `minio123` | MinIO 密码 |

---

## 📄 License

MIT
