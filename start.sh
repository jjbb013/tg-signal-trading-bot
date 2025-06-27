#!/bin/bash

echo "🚀 启动 Telegram 监听机器人..."

# 检查配置文件是否存在
if [ ! -f "telegram_config.json" ]; then
    echo "❌ 错误: 找不到 telegram_config.json 配置文件"
    echo "请先创建配置文件，然后重新启动"
    exit 1
fi

# 检查session文件是否存在
SESSION_FILES=$(ls session_*.session 2>/dev/null | wc -l)
if [ $SESSION_FILES -eq 0 ]; then
    echo "⚠️  警告: 没有找到session文件，需要先登录Telegram"
    echo "请运行: python login_telegram.py"
    echo "或者手动登录后重新启动"
    exit 1
fi

echo "✅ 配置文件检查通过"
echo "✅ Session文件存在"

# 启动应用
echo "🌐 启动Web服务器..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 