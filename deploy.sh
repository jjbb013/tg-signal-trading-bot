#!/bin/bash

# Northflank自动部署脚本
# 使用方法: ./deploy.sh

echo "🚀 开始部署到 Northflank..."

# 检查是否安装了Northflank CLI
if ! command -v northflank &> /dev/null; then
    echo "❌ 错误: 未安装Northflank CLI"
    echo "请先安装: npm install -g @northflank/cli"
    exit 1
fi

# 检查是否已登录
if ! northflank auth:status &> /dev/null; then
    echo "❌ 错误: 未登录Northflank"
    echo "请先登录: northflank auth:login"
    exit 1
fi

# 获取当前分支
BRANCH=$(git branch --show-current)
echo "📦 当前分支: $BRANCH"

# 推送代码到GitHub
echo "📤 推送代码到GitHub..."
git push origin $BRANCH

# 等待几秒让GitHub处理
echo "⏳ 等待GitHub处理..."
sleep 5

# 触发Northflank部署
echo "🔄 触发Northflank部署..."
northflank service:deploy

echo "✅ 部署完成！"
echo "🌐 访问你的应用: https://your-app.northflank.app" 