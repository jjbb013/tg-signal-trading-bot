#!/bin/bash

# 快速修复数据库权限脚本
# 在 Northflank 容器中运行此脚本来解决数据库权限问题

echo "=== 数据库权限修复脚本 ==="

# 创建数据目录
echo "创建数据目录..."
mkdir -p /data/sessions /data/logs

# 设置目录权限
echo "设置目录权限..."
chmod 755 /data /data/sessions /data/logs

# 检查当前用户
echo "当前用户: $(whoami)"
echo "当前用户ID: $(id)"

# 如果数据库文件存在，设置权限
if [ -f "/data/trading_bot.db" ]; then
    echo "设置数据库文件权限..."
    chmod 644 /data/trading_bot.db
fi

# 设置环境变量
export DATABASE_URL="sqlite:////data/trading_bot.db"

# 测试数据库连接
echo "测试数据库连接..."
python -c "
import sqlite3
try:
    conn = sqlite3.connect('/data/trading_bot.db')
    print('数据库连接成功')
    conn.close()
except Exception as e:
    print(f'数据库连接失败: {e}')
"

# 测试 SQLAlchemy
echo "测试 SQLAlchemy..."
python -c "
try:
    from models import engine
    print('SQLAlchemy 引擎创建成功')
except Exception as e:
    print(f'SQLAlchemy 引擎创建失败: {e}')
"

echo "=== 修复完成 ===" 