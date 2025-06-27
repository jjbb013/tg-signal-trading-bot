#!/bin/bash

echo "🚀 简化部署脚本"
echo "================"

# 检查配置文件
if [ ! -f ".northflank-config" ]; then
    echo "❌ 未找到配置文件 .northflank-config"
    echo "请先创建配置文件："
    echo ""
    echo "cat > .northflank-config << EOF"
    echo "NORTHFLANK_TOKEN=你的API_TOKEN"
    echo "NORTHFLANK_PROJECT_ID=你的项目ID"
    echo "NORTHFLANK_SERVICE_ID=你的服务ID"
    echo "EOF"
    echo ""
    echo "请参考 get-northflank-info.md 获取这些信息"
    exit 1
fi

# 加载配置
source .northflank-config

# 检查配置
if [ -z "$NORTHFLANK_TOKEN" ] || [ -z "$NORTHFLANK_PROJECT_ID" ] || [ -z "$NORTHFLANK_SERVICE_ID" ]; then
    echo "❌ 配置文件不完整"
    echo "请检查 .northflank-config 文件"
    exit 1
fi

echo "✅ 配置加载成功"
echo "📦 项目ID: $NORTHFLANK_PROJECT_ID"
echo "🔧 服务ID: $NORTHFLANK_SERVICE_ID"
echo ""

# 推送代码
echo "📤 推送代码到GitHub..."
git push origin main

if [ $? -ne 0 ]; then
    echo "❌ 推送代码失败"
    exit 1
fi

echo "✅ 代码推送成功"
echo ""

# 等待几秒
echo "⏳ 等待GitHub处理..."
sleep 5

# 触发部署
echo "🔄 触发Northflank部署..."
DEPLOY_URL="https://api.northflank.com/v1/projects/$NORTHFLANK_PROJECT_ID/services/$NORTHFLANK_SERVICE_ID/deployments"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $NORTHFLANK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"branch\": \"main\",
    \"commitSha\": \"$(git rev-parse HEAD)\",
    \"message\": \"Manual deploy from script - $(date)\"
  }" \
  "$DEPLOY_URL")

# 解析响应
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ 部署请求已发送"
    echo "📋 响应: $RESPONSE_BODY"
    echo ""
    echo "🎉 部署完成！"
    echo "🌐 访问你的应用: https://your-app.northflank.app"
else
    echo "❌ 部署失败"
    echo "📋 响应代码: $HTTP_CODE"
    echo "📋 响应内容: $RESPONSE_BODY"
    exit 1
fi 