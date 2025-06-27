#!/bin/bash

echo "🔧 Northflank 自动部署配置工具"
echo "=================================="

# 检查是否安装了Northflank CLI
if ! command -v northflank &> /dev/null; then
    echo "❌ 未安装Northflank CLI"
    echo "请先安装: npm install -g @northflank/cli"
    exit 1
fi

# 检查是否已登录
if ! northflank auth:status &> /dev/null; then
    echo "❌ 未登录Northflank"
    echo "请先登录: northflank auth:login"
    exit 1
fi

echo "✅ Northflank CLI 已安装并已登录"
echo ""

# 获取项目列表
echo "📋 获取项目列表..."
PROJECTS=$(northflank project:list --output json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ 获取项目列表失败"
    exit 1
fi

echo "找到以下项目:"
echo "$PROJECTS" | jq -r '.[] | "  - \(.name) (ID: \(.id))"'
echo ""

# 获取服务列表
echo "📋 获取服务列表..."
SERVICES=$(northflank service:list --output json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ 获取服务列表失败"
    exit 1
fi

echo "找到以下服务:"
echo "$SERVICES" | jq -r '.[] | "  - \(.name) (ID: \(.id), 项目ID: \(.projectId))"'
echo ""

# 获取API Token
echo "🔑 获取API Token..."
TOKEN=$(northflank auth:token 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ 获取API Token失败"
    exit 1
fi

echo "✅ 成功获取配置信息"
echo ""
echo "📝 请在GitHub仓库中设置以下Secrets:"
echo ""
echo "NORTHFLANK_TOKEN:"
echo "$TOKEN"
echo ""
echo "NORTHFLANK_PROJECT_ID: 从上面的项目列表中选择"
echo "NORTHFLANK_SERVICE_ID: 从上面的服务列表中选择"
echo ""
echo "🔗 设置步骤:"
echo "1. 进入GitHub仓库"
echo "2. 点击 Settings → Secrets and variables → Actions"
echo "3. 点击 'New repository secret'"
echo "4. 添加上述三个secrets"
echo ""
echo "🎉 配置完成后，每次推送代码到main分支都会自动部署！" 