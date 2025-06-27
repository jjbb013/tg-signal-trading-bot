# Telegram监听机器人部署指南

## 🚀 自动部署方案

本项目支持三种自动部署方案：

### 方案1: GitHub Actions (推荐)

**优点**: 完全自动化，代码推送即部署
**缺点**: 需要配置GitHub Secrets

#### 配置步骤:

1. **在GitHub仓库中设置Secrets**:
   - 进入你的GitHub仓库
   - 点击 Settings → Secrets and variables → Actions
   - 添加以下Secrets:
     ```
     NORTHFLANK_TEAM_ID=jjbb013s-team
     NORTHFLANK_PROJECT_ID=tglisten
     NORTHFLANK_SERVICE_ID=tgl
     NORTHFLANK_TOKEN=nf-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiMGUyZTRiMzYtYjQyYS00NTVhLWJlNTUtZGYzZGE4MGZkNzY1IiwiaWF0IjoxNzUwOTk5OTIyfQ.W_E5VmoHzhXyiq2sjf1lfTHYIRPOonmlH6irXT86JSg
     ```

2. **推送代码触发部署**:
   ```bash
   git add .
   git commit -m "更新代码"
   git push origin main
   ```

3. **查看部署状态**:
   - 在GitHub仓库页面点击 Actions 标签
   - 查看最新的部署工作流

### 方案2: 本地脚本部署

**优点**: 简单直接，无需GitHub配置
**缺点**: 需要手动执行

#### 使用步骤:

1. **确保配置文件存在**:
   ```bash
   # 检查配置文件
   cat .northflank-config
   ```

2. **执行部署脚本**:
   ```bash
   chmod +x simple-deploy.sh
   ./simple-deploy.sh
   ```

### 方案3: Northflank内置Auto Deploy

**优点**: 无需额外配置
**缺点**: 需要手动开启

#### 配置步骤:

1. 登录Northflank控制台
2. 进入你的项目和服务
3. 在服务设置中找到 "Auto Deploy" 选项
4. 开启并配置GitHub仓库连接

## 🔧 部署前检查清单

### 必需文件检查:
- [x] `main.py` - FastAPI应用主文件
- [x] `requirements.txt` - Python依赖
- [x] `Dockerfile` - 容器配置
- [x] `.github/workflows/deploy.yml` - GitHub Actions工作流
- [x] `simple-deploy.sh` - 本地部署脚本
- [x] `.northflank-config` - Northflank配置

### 配置检查:
- [x] Northflank团队ID: `jjbb013s-team`
- [x] Northflank项目ID: `tglisten`
- [x] Northflank服务ID: `tgl`
- [x] API Token已配置

## 🐛 常见问题解决

### 1. 部署失败 - API路径错误
**错误**: `404 Not Found`
**解决**: 确保API路径包含团队ID:
```
https://api.northflank.com/v1/projects/{TEAM_ID}/{PROJECT_ID}/services/{SERVICE_ID}/deployments
```

### 2. 认证失败
**错误**: `401 Unauthorized`
**解决**: 
- 检查API Token是否正确
- 确认Token未过期
- 验证Token有部署权限

### 3. 权限不足
**错误**: `403 Forbidden`
**解决**:
- 确认Token有项目访问权限
- 检查团队和项目ID是否正确

### 4. 构建失败
**错误**: Docker构建失败
**解决**:
- 检查Dockerfile语法
- 确认requirements.txt中的依赖正确
- 查看Northflank构建日志

## 📊 部署状态监控

### 查看部署状态:
1. **Northflank控制台**: https://app.northflank.com/t/jjbb013s-team/project/tglisten/services/tgl
2. **GitHub Actions**: 仓库 → Actions标签
3. **应用访问**: 部署完成后通过Northflank提供的URL访问

### 日志查看:
- **应用日志**: Northflank控制台 → 服务 → Logs
- **构建日志**: Northflank控制台 → 服务 → Deployments → 查看构建日志

## 🔄 更新部署

### 代码更新后重新部署:
1. **GitHub Actions**: 推送代码到main分支自动触发
2. **本地脚本**: 运行 `./simple-deploy.sh`
3. **手动触发**: 在Northflank控制台手动触发部署

### 配置更新:
- 修改 `.northflank-config` 文件
- 更新GitHub Secrets (如果使用GitHub Actions)
- 重新部署

## 📞 技术支持

如果遇到部署问题:
1. 检查Northflank控制台的错误日志
2. 查看GitHub Actions的执行日志
3. 确认所有配置信息正确
4. 参考Northflank官方文档

## 🎯 成功部署标志

部署成功后，你应该能够:
1. 在Northflank控制台看到服务状态为"Running"
2. 通过提供的URL访问Web界面
3. 在GitHub Actions中看到部署成功状态
4. 应用能够正常启动并响应请求 