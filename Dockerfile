# 基于官方Python 3.11精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 默认启动bash，便于SSH登录后手动运行监听/登录脚本
CMD ["bash"] 