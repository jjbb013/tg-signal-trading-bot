FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# 安装 supervisor
RUN apt-get update && apt-get install -y supervisor

# 创建日志和数据目录（如已存在不会报错）
RUN mkdir -p /app/logs /app/data /app/data/sessions

# 设置环境变量（可根据需要修改）
ENV PYTHONUNBUFFERED=1

CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"] 