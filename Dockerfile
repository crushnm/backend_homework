# 使用官方Python镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装UV并设置PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 复制项目文件
COPY backend/pyproject.toml backend/uv.lock* ./

# 安装Python依赖（使用完整路径确保找到uv）
RUN /root/.local/bin/uv sync --no-dev

# 复制源代码
COPY backend/src ./src
COPY backend/.env.example ./.env

# 暴露端口
EXPOSE 8000

# 启动命令（使用完整路径）
CMD ["/root/.local/bin/uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
