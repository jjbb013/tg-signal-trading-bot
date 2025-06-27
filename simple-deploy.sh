#!/bin/bash

echo "🚀 简化部署脚本"
echo "================"

# 检查配置文件
if [ ! -f ".northflank-config" ]; then
    echo "❌ 未找到配置文件 .northflank-config"
    echo "请先创建配置文件："
    echo ""
    echo "cat > .northflank-config << EOF"
    echo "NORTHFLANK_TEAM_ID=你的团队ID"
    echo "NORTHFLANK_PROJECT_ID=你的项目ID"
    echo "NORTHFLANK_SERVICE_ID=你的服务ID"
    echo "NORTHFLANK_TOKEN=你的API_TOKEN"
    echo "EOF"
    echo ""
    echo "请参考 get-northflank-info.md 获取这些信息"
    exit 1
fi

# 加载配置
source .northflank-config

# 检查配置
if [ -z "$NORTHFLANK_TOKEN" ] || [ -z "$NORTHFLANK_TEAM_ID" ] || [ -z "$NORTHFLANK_PROJECT_ID" ] || [ -z "$NORTHFLANK_SERVICE_ID" ]; then
    echo "❌ 配置文件不完整"
    echo "请检查 .northflank-config 文件"
    echo "需要包含: NORTHFLANK_TEAM_ID, NORTHFLANK_PROJECT_ID, NORTHFLANK_SERVICE_ID, NORTHFLANK_TOKEN"
    exit 1
fi

echo "✅ 配置加载成功"
echo "👥 团队ID: $NORTHFLANK_TEAM_ID"
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
DEPLOY_URL="https://api.northflank.com/v1/projects/$NORTHFLANK_TEAM_ID/$NORTHFLANK_PROJECT_ID/services/$NORTHFLANK_SERVICE_ID/deployments"

echo "📡 请求URL: $DEPLOY_URL"
echo "🔑 使用Token: ${NORTHFLANK_TOKEN:0:20}..."

# 使用临时文件存储响应
TEMP_RESPONSE=$(mktemp)
TEMP_HEADERS=$(mktemp)

RESPONSE=$(curl -s -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $NORTHFLANK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"branch\": \"main\",
    \"commitSha\": \"$(git rev-parse HEAD)\",
    \"message\": \"Manual deploy from script - $(date)\"
  }" \
  "$DEPLOY_URL" \
  -o "$TEMP_RESPONSE" \
  -D "$TEMP_HEADERS")

# 读取响应内容
RESPONSE_BODY=$(cat "$TEMP_RESPONSE")
HTTP_CODE="$RESPONSE"

echo "📋 响应代码: $HTTP_CODE"
echo "📋 响应内容: $RESPONSE_BODY"

# 清理临时文件
rm -f "$TEMP_RESPONSE" "$TEMP_HEADERS"

if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ 部署请求已发送"
    echo ""
    echo "🎉 部署完成！"
    echo "🌐 访问你的应用: https://app.northflank.com/t/$NORTHFLANK_TEAM_ID/project/$NORTHFLANK_PROJECT_ID/services/$NORTHFLANK_SERVICE_ID"
else
    echo "❌ 部署失败"
    echo ""
    echo "🔍 可能的原因："
    echo "1. 团队ID、项目ID或服务ID不正确"
    echo "2. API Token无效或过期"
    echo "3. 权限不足"
    echo "4. API路径格式错误"
    echo ""
    echo "💡 建议："
    echo "1. 检查Northflank控制台中的URL格式"
    echo "2. 重新生成API Token"
    echo "3. 确认Token有部署权限"
    echo "4. 检查API文档确认路径格式"
    exit 1
fi 