# 部署指南

本文档介绍 Paperlib MCP 的多种部署方式。

## 部署方式对比

| 方式 | 难度 | 适用场景 |
|------|------|---------|
| [Docker Compose](#方式-1-docker-compose-推荐) | ⭐ | 快速体验、开发测试 |
| [PyPI 安装](#方式-2-pypi-安装) | ⭐⭐ | 使用现有数据库 |
| [Kubernetes](#方式-3-kubernetes) | ⭐⭐⭐ | 生产环境 |

---

## 方式 1: Docker Compose (推荐)

一键启动完整环境，包含 PostgreSQL + MinIO + MCP Server。

### 前置要求

- Docker 20.10+
- Docker Compose v2+
- OpenRouter API Key

### 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/paperlib-mcp.git
cd paperlib-mcp

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 OPENROUTER_API_KEY

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f paperlib-mcp
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 数据库 |
| MinIO API | 9000 | 对象存储 |
| MinIO Console | 9001 | Web 管理界面 |
| Adminer | 8080 | 数据库管理 (可选) |

### 启用可选服务

```bash
# 启用 Adminer 数据库管理界面
docker-compose --profile admin up -d
```

### 连接 MCP 客户端

由于 MCP 使用 STDIO 模式，需要从容器内运行：

```bash
# 进入容器执行 MCP 命令
docker exec -it paperlib-mcp python -m paperlib_mcp.server
```

或者配置客户端直接使用 Docker：

```json
{
  "mcpServers": {
    "paperlib": {
      "command": "docker",
      "args": ["exec", "-i", "paperlib-mcp", "python", "-m", "paperlib_mcp.server"]
    }
  }
}
```

---

## 方式 2: PyPI 安装

适合已有 PostgreSQL 和 MinIO 的用户。

### 前置要求

- Python 3.11+
- PostgreSQL 16+ with pgvector
- MinIO 或 S3 兼容存储
- OpenRouter API Key

### 安装

```bash
# 使用 pip
pip install paperlib-mcp

# 或使用 uv
uv pip install paperlib-mcp
```

### 配置

设置环境变量：

```bash
export POSTGRES_HOST=your-postgres-host
export POSTGRES_USER=paper
export POSTGRES_PASSWORD=your-password
export POSTGRES_DB=paperlib

export S3_ENDPOINT=http://your-minio:9000
export MINIO_ROOT_USER=your-access-key
export MINIO_ROOT_PASSWORD=your-secret-key

export OPENROUTER_API_KEY=your-api-key
```

### 初始化数据库

```bash
# 下载并执行迁移脚本
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f initdb/001_schema.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f initdb/002_m1_migration.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f initdb/003_m2_graphrag.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f initdb/004_m3_review.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f initdb/004_m4_canonicalization.sql
```

### 运行

```bash
# STDIO 模式
python -m paperlib_mcp.server

# 或使用 uvx
uvx paperlib-mcp
```

### IDE 配置

**Cursor / Claude Desktop:**

```json
{
  "mcpServers": {
    "paperlib": {
      "command": "python",
      "args": ["-m", "paperlib_mcp.server"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "OPENROUTER_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## 方式 3: Kubernetes

生产环境部署示例。

### 前置要求

- Kubernetes 1.24+
- Helm 3+
- kubectl

### 部署步骤

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: paperlib-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: paperlib-mcp
  template:
    metadata:
      labels:
        app: paperlib-mcp
    spec:
      containers:
      - name: paperlib-mcp
        image: your-registry/paperlib-mcp:latest
        envFrom:
        - secretRef:
            name: paperlib-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### 使用现有云服务

| 云服务 | PostgreSQL | 对象存储 |
|--------|-----------|---------|
| AWS | RDS for PostgreSQL | S3 |
| GCP | Cloud SQL | Cloud Storage |
| Azure | Azure Database | Blob Storage |

---

## 环境变量参考

### 必需变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | `sk-or-...` |

### PostgreSQL

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_HOST` | `localhost` | 主机地址 |
| `POSTGRES_PORT` | `5432` | 端口 |
| `POSTGRES_USER` | `paper` | 用户名 |
| `POSTGRES_PASSWORD` | `paper` | 密码 |
| `POSTGRES_DB` | `paperlib` | 数据库名 |

### MinIO / S3

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `S3_ENDPOINT` | `http://localhost:9000` | API 端点 |
| `MINIO_ROOT_USER` | `minio` | Access Key |
| `MINIO_ROOT_PASSWORD` | `minio123` | Secret Key |
| `MINIO_BUCKET` | `papers` | 存储桶名 |

### LLM 模型

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | 嵌入模型 |
| `LLM_MODEL` | `openai/gpt-4o-mini` | LLM 模型 |
| `EMBEDDING_BATCH_SIZE` | `64` | 批处理大小 |

---

## 故障排除

### 无法连接 PostgreSQL

```bash
# 检查连接
docker exec -it paperlib-postgres psql -U paper -d paperlib -c "SELECT 1"

# 检查 pgvector 扩展
docker exec -it paperlib-postgres psql -U paper -d paperlib -c "SELECT * FROM pg_extension"
```

### 无法连接 MinIO

```bash
# 检查 bucket
docker exec -it paperlib-minio mc ls local/papers

# 检查健康状态
curl http://localhost:9000/minio/health/live
```

### MCP 工具不可用

```bash
# 检查 MCP 服务器
docker exec -it paperlib-mcp python -c "from paperlib_mcp.db import check_connection; print(check_connection())"
```

---

## 备份与恢复

### 备份

```bash
# 备份 PostgreSQL
docker exec paperlib-postgres pg_dump -U paper paperlib > backup.sql

# 备份 MinIO
docker run --rm -v paperlib_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio-backup.tar.gz /data
```

### 恢复

```bash
# 恢复 PostgreSQL
cat backup.sql | docker exec -i paperlib-postgres psql -U paper paperlib

# 恢复 MinIO
docker run --rm -v paperlib_minio_data:/data -v $(pwd):/backup alpine tar xzf /backup/minio-backup.tar.gz -C /
```
