#!/bin/bash

echo "🔍 检查Northflank项目配置"
echo "========================"

# 检查配置文件
if [ ! -f ".northflank-config" ]; then
    echo "❌ 未找到配置文件 .northflank-config"
    exit 1
fi

# 加载配置
source .northflank-config

echo "✅ 配置加载成功"
echo "👥 团队ID: $NORTHFLANK_TEAM_ID"
echo "📦 项目ID: $NORTHFLANK_PROJECT_ID"
echo "🔧 服务ID: $NORTHFLANK_SERVICE_ID"
echo ""

# 检查项目信息
echo "📋 检查项目信息..."
PROJECT_URL="https://api.northflank.com/v1/projects/$NORTHFLANK_PROJECT_ID"

PROJECT_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $NORTHFLANK_TOKEN" \
  "$PROJECT_URL")

PROJECT_HTTP_CODE=$(echo "$PROJECT_RESPONSE" | tail -n1)
PROJECT_BODY=$(echo "$PROJECT_RESPONSE" | sed '$d')

echo "📋 项目响应代码: $PROJECT_HTTP_CODE"
if [ "$PROJECT_HTTP_CODE" -eq 200 ]; then
    echo "✅ 项目存在"
    echo "📋 项目信息: $PROJECT_BODY"
else
    echo "❌ 项目不存在或无法访问"
    echo "📋 错误信息: $PROJECT_BODY"
fi
echo ""

# 检查服务信息
echo "📋 检查服务信息..."
SERVICE_URL="https://api.northflank.com/v1/projects/$NORTHFLANK_PROJECT_ID/services/$NORTHFLANK_SERVICE_ID"

SERVICE_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $NORTHFLANK_TOKEN" \
  "$SERVICE_URL")

SERVICE_HTTP_CODE=$(echo "$SERVICE_RESPONSE" | tail -n1)
SERVICE_BODY=$(echo "$SERVICE_RESPONSE" | sed '$d')

echo "📋 服务响应代码: $SERVICE_HTTP_CODE"
if [ "$SERVICE_HTTP_CODE" -eq 200 ]; then
    echo "✅ 服务存在"
    echo "📋 服务信息: $SERVICE_BODY"
    
    # 检查服务类型 - 使用更准确的JSON解析
    SERVICE_TYPE=$(echo "$SERVICE_BODY" | grep -o '"serviceType":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "🔧 服务类型: $SERVICE_TYPE"
    
    if [ "$SERVICE_TYPE" = "deployment" ]; then
        echo "✅ 这是部署服务，可以使用自动部署API"
    elif [ "$SERVICE_TYPE" = "build" ]; then
        echo "⚠️  这是构建服务，需要创建部署服务才能使用自动部署API"
        echo "💡 建议：在Northflank控制台创建一个Deployment Service"
    elif [ "$SERVICE_TYPE" = "combined" ]; then
        echo "⚠️  这是组合服务，自动部署API可能不兼容"
        echo "💡 建议：创建单独的Deployment Service"
    else
        echo "❓ 未知服务类型: $SERVICE_TYPE"
    fi
else
    echo "❌ 服务不存在或无法访问"
    echo "📋 错误信息: $SERVICE_BODY"
fi
echo ""

# 列出所有服务
echo "📋 列出项目中的所有服务..."
SERVICES_URL="https://api.northflank.com/v1/projects/$NORTHFLANK_PROJECT_ID/services"

SERVICES_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $NORTHFLANK_TOKEN" \
  "$SERVICES_URL")

SERVICES_HTTP_CODE=$(echo "$SERVICES_RESPONSE" | tail -n1)
SERVICES_BODY=$(echo "$SERVICES_RESPONSE" | sed '$d')

echo "📋 服务列表响应代码: $SERVICES_HTTP_CODE"
if [ "$SERVICES_HTTP_CODE" -eq 200 ]; then
    echo "✅ 获取服务列表成功"
    echo "📋 服务列表: $SERVICES_BODY"
else
    echo "❌ 无法获取服务列表"
    echo "📋 错误信息: $SERVICES_BODY"
fi 