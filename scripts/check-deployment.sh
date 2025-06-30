#!/bin/bash

# Northflank 部署检查脚本
# 用于检查部署状态和数据持久化

echo "=== Northflank 部署状态检查 ==="

# 检查环境变量
echo "1. 检查环境变量..."
if [ -n "$TG_API_ID" ]; then
    echo "✓ TG_API_ID 已设置"
else
    echo "✗ TG_API_ID 未设置"
fi

if [ -n "$TG_API_HASH" ]; then
    echo "✓ TG_API_HASH 已设置"
else
    echo "✗ TG_API_HASH 未设置"
fi

if [ -n "$TG_PHONE_NUMBER" ]; then
    echo "✓ TG_PHONE_NUMBER 已设置: $TG_PHONE_NUMBER"
else
    echo "✗ TG_PHONE_NUMBER 未设置"
fi

if [ -n "$TG_GROUP_IDS" ]; then
    echo "✓ TG_GROUP_IDS 已设置: $TG_GROUP_IDS"
else
    echo "✗ TG_GROUP_IDS 未设置"
fi

# 检查数据目录
echo ""
echo "2. 检查数据目录..."
DATA_PATH="${DATA_PATH:-/data}"

if [ -d "$DATA_PATH" ]; then
    echo "✓ 数据目录存在: $DATA_PATH"
else
    echo "✗ 数据目录不存在: $DATA_PATH"
fi

if [ -d "$DATA_PATH/sessions" ]; then
    echo "✓ Sessions目录存在"
    ls -la "$DATA_PATH/sessions/"
else
    echo "✗ Sessions目录不存在"
fi

if [ -d "$DATA_PATH/logs" ]; then
    echo "✓ Logs目录存在"
    ls -la "$DATA_PATH/logs/"
else
    echo "✗ Logs目录不存在"
fi

# 检查数据库
echo ""
echo "3. 检查数据库..."
if [ -f "$DATA_PATH/trading_bot.db" ]; then
    echo "✓ 数据库文件存在"
    echo "数据库大小: $(du -h "$DATA_PATH/trading_bot.db" | cut -f1)"
else
    echo "✗ 数据库文件不存在"
fi

# 检查Session文件
echo ""
echo "4. 检查Session文件..."
SESSION_FILE="$DATA_PATH/sessions/session_$TG_PHONE_NUMBER.session"
if [ -f "$SESSION_FILE" ]; then
    echo "✓ Session文件存在: $SESSION_FILE"
    echo "Session文件大小: $(du -h "$SESSION_FILE" | cut -f1)"
else
    echo "✗ Session文件不存在: $SESSION_FILE"
    echo "需要执行首次登录: python main.py --login"
fi

# 检查进程
echo ""
echo "5. 检查进程状态..."
if pgrep -f "python main.py" > /dev/null; then
    echo "✓ 机器人进程正在运行"
    ps aux | grep "python main.py" | grep -v grep
else
    echo "✗ 机器人进程未运行"
fi

# 检查PID文件
PID_FILE="$DATA_PATH/tg_bot.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "✓ PID文件存在: $PID"
    if kill -0 "$PID" 2>/dev/null; then
        echo "✓ 进程 $PID 正在运行"
    else
        echo "✗ 进程 $PID 未运行"
    fi
else
    echo "✗ PID文件不存在"
fi

# 检查API服务
echo ""
echo "6. 检查API服务..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ API服务正在运行"
    curl -s http://localhost:8000/api/health | python -m json.tool
else
    echo "✗ API服务未运行"
fi

echo ""
echo "=== 检查完成 ===" 