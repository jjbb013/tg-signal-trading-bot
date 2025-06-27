# Northflank 配置信息获取指南

由于无法找到Auto Deploy选项，我们使用GitHub Actions来实现自动部署。

## 方法一：从Northflank控制台获取信息

### 1. 获取项目ID
1. 登录Northflank控制台
2. 进入你的项目
3. 查看浏览器地址栏，URL格式类似：
   ```
   https://app.northflank.com/projects/[项目ID]/services
   ```
4. 复制 `[项目ID]` 部分

### 2. 获取服务ID
1. 点击你的Service
2. 查看浏览器地址栏，URL格式类似：
   ```
   https://app.northflank.com/projects/[项目ID]/services/[服务ID]
   ```
3. 复制 `[服务ID]` 部分

### 3. 获取API Token
1. 在Northflank控制台右上角点击你的头像
2. 选择 `Account Settings` 或 `Profile`
3. 找到 `API Tokens` 或 `Access Tokens` 部分
4. 创建新的API Token
5. 复制生成的Token

## 方法二：使用浏览器开发者工具

### 1. 打开开发者工具
- 在Northflank控制台按 `F12` 或右键选择"检查"
- 切换到 `Network` 标签页

### 2. 获取项目信息
1. 刷新页面
2. 在Network标签页中找到API请求
3. 查找包含项目信息的请求
4. 从响应中提取项目ID和服务ID

### 3. 获取Token
1. 在Network标签页中查找认证请求
2. 找到包含Authorization头的请求
3. 复制Bearer Token

## 配置GitHub Secrets

获取到信息后，在GitHub仓库中设置Secrets：

1. **进入GitHub仓库**
2. **点击 Settings → Secrets and variables → Actions**
3. **点击 "New repository secret"**
4. **添加以下三个secrets：**

   - **Name**: `NORTHFLANK_TOKEN`
   - **Value**: 你的API Token

   - **Name**: `NORTHFLANK_PROJECT_ID`
   - **Value**: 你的项目ID

   - **Name**: `NORTHFLANK_SERVICE_ID`
   - **Value**: 你的服务ID

## 测试自动部署

配置完成后：

1. **推送代码到main分支**
   ```bash
   git add .
   git commit -m "测试自动部署"
   git push origin main
   ```

2. **检查GitHub Actions**
   - 进入GitHub仓库
   - 点击 `Actions` 标签页
   - 查看部署进度

3. **检查Northflank**
   - 登录Northflank控制台
   - 查看Service的部署历史
   - 确认新版本已部署

## 故障排除

### 如果获取信息失败：
1. 检查Northflank账户权限
2. 确认项目和服务存在
3. 尝试重新登录Northflank

### 如果部署失败：
1. 检查GitHub Secrets是否正确
2. 查看GitHub Actions的错误日志
3. 确认API Token有足够权限

## 手动部署（备用方案）

如果自动部署有问题，可以使用手动部署：

```bash
# 推送代码
git push origin main

# 在Northflank控制台手动触发重新部署
# 或者使用部署脚本
./deploy.sh
``` 