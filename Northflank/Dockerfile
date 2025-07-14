# 使用官方 Python 3.11 slim 作为基础镜像
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 安装 supervisor
RUN apt-get update && apt-get install -y supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 创建持久化目录（可被 Northflank 卷覆盖）
RUN mkdir -p /app/data/sessions /app/logs

COPY . .

CMD ["bash", "start.sh"] 