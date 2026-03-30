# 多阶段构建：第一阶段 - 构建依赖
FROM python:3.11-slim as builder

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升级pip并安装依赖
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir aiosqlite \
    && pip install --no-cache-dir -r requirements.txt

# 第二阶段 - 运行环境
FROM python:3.11-slim

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/config

# 创建非root用户
RUN groupadd -r oilmonitor && useradd -r -g oilmonitor oilmonitor \
    && chown -R oilmonitor:oilmonitor /app
USER oilmonitor

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令 - 使用uvicorn
CMD ["uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]