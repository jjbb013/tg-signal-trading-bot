#!/bin/bash

# Northflank 启动脚本
# 用于在 Northflank 环境中启动 Telegram 交易机器人

set -e

echo "=== Telegram 交易机器人启动脚本 ==="
echo "数据存储路径: $DATA_PATH"
echo "Session文件路径: $SESSION_FILE"
echo "日志路径: $LOGS_PATH"
echo "数据库路径: $DB_PATH"

# 确保目录存在
mkdir -p "$DATA_PATH/sessions"
mkdir -p "$DATA_PATH/logs"

# 确保数据目录存在并有正确权限
mkdir -p /data/sessions /data/logs
chmod 755 /data /data/sessions /data/logs

# 设置数据库环境变量
export DATABASE_URL="sqlite:////data/trading_bot.db"

echo "目录创建完成"

# 检查环境变量
if [ -z "$TG_API_ID" ] || [ -z "$TG_API_HASH" ] || [ -z "$TG_PHONE_NUMBER" ]; then
    echo "错误: 缺少必要的环境变量"
    echo "请确保设置了 TG_API_ID, TG_API_HASH, TG_PHONE_NUMBER"
    exit 1
fi

echo "环境变量检查通过"

# 检查是否需要登录
SESSION_FILE="$DATA_PATH/sessions/session_$TG_PHONE_NUMBER.session"
if [ ! -f "$SESSION_FILE" ]; then
    echo "Session文件不存在，需要首次登录"
    echo "请通过 Web 终端执行: python main.py --login"
    echo "或者等待自动登录流程"
fi

# 启动机器人
echo "启动 Telegram 交易机器人..."
exec python main.py --daemon 

# 启动应用
exec "$@" 