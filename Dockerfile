# 基于官方Python 3.11精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装supervisor
RUN apt-get update && apt-get install -y supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 创建数据目录
RUN mkdir -p /data/sessions /data/logs

# 复制项目代码和supervisor配置
COPY . .

# 设置执行权限
RUN chmod +x /app/init_db.py

# 暴露web终端端口
EXPOSE 8080

# 启动命令：先初始化数据库，然后启动supervisor
CMD ["sh", "-c", "python /app/init_db.py && supervisord -c /app/supervisord.conf"] 