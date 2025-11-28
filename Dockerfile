# 使用官方Python镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装UV并设置PATH
RUN pip install --upgrade pip && pip install uv

# 复制项目文件
COPY backend/pyproject.toml backend/uv.lock* ./

#复制源代码(必须在安装依赖前完成，因为本地包需要这些文件)
COPY backend/src ./src
COPY backend/README.md ./README.md
COPY backend/.env.example ./.env


# 安装Python依赖（使用完整路径确保找到uv）
RUN uv sync --no-dev

# 复制前端静态文件
COPY frontend ./static

# 暴露端口
EXPOSE 8000

# 启动命令（使用完整路径）
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
