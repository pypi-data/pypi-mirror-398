# Paperlib MCP

Academic literature management and retrieval MCP server - supporting PDF import, hybrid search, knowledge graph construction, and literature review generation.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文 README](./README_CN.md)

## ✨ Features

| Feature | Description |
|---------|-------------|
| **PDF Import** | Auto-extract text, chunk by page, generate vector embeddings |
| **Hybrid Search** | FTS full-text search + pgvector semantic search |
| **Knowledge Graph** | LLM-driven entity/relation/claim extraction, Leiden community detection |
| **Review Generation** | Structured literature review auto-generation based on evidence packs |

## 📋 Prerequisites

- PostgreSQL 16+ with pgvector extension
- MinIO or S3-compatible storage
- OpenRouter API Key

---

## 🚀 Installation & Usage

### Method 1: Docker Compose (Recommended for Beginners)

One-click launch of complete environment (PostgreSQL + MinIO + MCP):

```bash
git clone https://github.com/your-org/paperlib-mcp.git
cd paperlib-mcp

# Configure API Key
cp .env.example .env
# Edit .env and fill in OPENROUTER_API_KEY

# Start services
docker-compose up -d
```

#### Configure in Cursor

Add to `claude_desktop_config.json`:

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


### Method 2: uvx Install (Recommended)

**Prerequisites**: Requires available PostgreSQL (with pgvector) and MinIO/S3-compatible storage service.

<details>
<summary>💡 Quick Start Local Services (Optional)</summary>

```bash
docker-compose up -d postgres minio minio-init
```
</details>

Configure in Cursor/Claude Desktop, modify environment variables according to your actual service addresses:

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

### Method 3: pip Install

**Prerequisites**: Same as Method 2, requires available PostgreSQL and MinIO/S3 services.

```bash
pip install paperlib-mcp
```

Configure MCP client (modify according to your actual service addresses):

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

### Method 4: Local Development

```bash
git clone https://github.com/your-org/paperlib-mcp.git
cd paperlib-mcp

uv sync
cp .env.example .env
# Edit .env

uv run python -m paperlib_mcp.server
```

---

## 📖 Available Tools

### Basic Tools
| Tool | Description |
|------|-------------|
| `health_check` | System health check |
| `import_pdf` | Import PDF documents |
| `download_pdf` | Download PDF by title to local directory |
| `search_hybrid` | Hybrid search (recommended) |
| `get_document` | Get document metadata |
| `list_documents` | List all documents |

### Graph Tools
| Tool | Description |
|------|-------------|
| `extract_graph_v1` | Extract knowledge graph |
| `build_communities_v1` | Build topic communities |
| `summarize_community_v1` | Generate community summaries |

### Writing Tools
| Tool | Description |
|------|-------------|
| `build_evidence_pack` | Build evidence pack |
| `draft_lit_review_v1` | Generate review draft |

> Full tool list (48+) available at [docs/MCP_TOOLS_REFERENCE.md](./docs/MCP_TOOLS_REFERENCE.md)

---

## 💡 Usage Examples

```bash
# Import PDF
> import_pdf file_path="/papers/study.pdf" title="Study Title"

# Search literature
> search_hybrid query="monetary policy" k=10

# Build knowledge graph
> extract_graph_v1 doc_id="abc123"
> build_communities_v1 level="macro"

# Generate review
> build_evidence_pack query="CBDC" k=40
> draft_lit_review_v1 pack_id=1
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Deployment Guide |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System Architecture |
| [EMBEDDING_SYSTEM.md](./docs/EMBEDDING_SYSTEM.md) | Embedding & Retrieval |
| [KNOWLEDGE_GRAPH.md](./docs/KNOWLEDGE_GRAPH.md) | Knowledge Graph |
| [DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md) | Database Schema |
| [MCP_TOOLS_REFERENCE.md](./docs/MCP_TOOLS_REFERENCE.md) | Tools API Reference |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| MCP Protocol | FastMCP |
| Database | PostgreSQL 16 + pgvector |
| Object Storage | MinIO (S3 Compatible) |
| PDF Processing | PyMuPDF4LLM |
| Embedding Model | OpenRouter (text-embedding-3-small) |
| Graph Clustering | igraph + Leiden |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ | - | OpenRouter API key |
| `POSTGRES_HOST` | ❌ | `localhost` | Database host |
| `POSTGRES_USER` | ❌ | `paper` | Database user |
| `POSTGRES_PASSWORD` | ❌ | `paper` | Database password |
| `POSTGRES_DB` | ❌ | `paperlib` | Database name |
| `S3_ENDPOINT` | ❌ | `http://localhost:9000` | MinIO endpoint |
| `MINIO_ROOT_USER` | ❌ | `minio` | MinIO user |
| `MINIO_ROOT_PASSWORD` | ❌ | `minio123` | MinIO password |

---

## 📄 License

MIT
