# 基于官方Python 3.11精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装shellinabox和supervisor
RUN apt-get update && apt-get install -y shellinabox supervisor \
    && echo "root:333333" | chpasswd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制项目代码和supervisor配置
COPY . .

# 暴露web终端端口
EXPOSE 8080

# 用supervisor同时管理监听和web终端
CMD ["supervisord", "-c", "/app/supervisord.conf"] 