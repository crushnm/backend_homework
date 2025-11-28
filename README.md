# Contoso Ltd 员工报销跟踪系统

这是一个为Contoso Ltd公司设计的员工报销跟踪系统，支持员工创建报销票据和雇主审批管理功能。

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + asyncpg
- **数据库**: PostgreSQL
- **前端**: HTML + JavaScript (Vanilla)
- **包管理**: Astral UV

## 功能特性

### 用户角色
- **员工**: 创建和查看自己的报销票据
- **雇主**: 查看所有票据、审批/驳回票据、管理员工账号

### 核心功能
- 邮箱密码登录/注册
- 报销票据管理（创建、查看、审批、驳回）
- 员工账号管理（暂停/激活）
- 密码哈希加密
- 异步并发处理

## 数据库搭建步骤

### 1. 安装 PostgreSQL

**Windows:**
```bash
# 下载并安装 PostgreSQL: https://www.postgresql.org/download/windows/
# 或使用 Chocolatey
choco install postgresql
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Mac (使用 Homebrew)
brew install postgresql
```

### 2. 创建数据库

```bash
# 启动 PostgreSQL 服务
# Windows: 通常自动启动
# Linux: sudo systemctl start postgresql
# Mac: brew services start postgresql

# 连接到 PostgreSQL
psql -U postgres

# 在 psql 中执行以下命令
CREATE DATABASE contoso_expense;
CREATE USER contoso_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE contoso_expense TO contoso_user;
# 连接到新数据库
\c contoso_expense
#授予schema权限
GRANT ALL ON SCHEMA public TO contoso_user;
\q
```

### 3. 配置环境变量

创建 `backend/.env` 文件：

```env
DATABASE_URL=postgresql+asyncpg://contoso_user:your_password@localhost/contoso_expense
SECRET_KEY=your-secret-key-change-this-in-production
```

## 依赖包安装与项目运行

### 1. 安装 UV

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装依赖

```bash
cd backend
uv sync
```

### 3. 初始化数据库

```bash
cd backend
uv run python scripts/init_db.py

```


### 4. 运行后端服务

```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

后端API将在 http://localhost:8000 运行
通过访问http://localhost:8000/static/index.html访问网站首页


## API 文档

启动后端后，访问以下地址查看自动生成的API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 运行测试

```bash
cd backend
uv run python -m unittest discover tests
```

测试包含链式集成测试，验证完整的用户流程。

### black格式化工具
```bash
#检查格式化
uv run black --check src tests
#进行black格式化
uv run black src tests
```

### Docker 部署

```bash
# 构建并启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

Docker部署会自动启动PostgreSQL和后端服务，前端可通过 http://localhost:8000/static/index.html 访问。
