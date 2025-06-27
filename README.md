# Telegram 极简监听机器人（Northflank部署版）

## 功能简介
- 监听多个Telegram群组消息，支持关键词自动Bark推送
- 所有配置通过环境变量注入，适合云端/容器部署
- 支持 Northflank 平台一键部署，SSH 登录后手动登录/启动监听
- 代码极简，无Web、无数据库、无代理

---

## 目录结构
- main.py                # 监听主程序（支持Bark推送）
- requirements.txt       # 依赖说明
- Dockerfile             # 部署文件
- README.md              # 使用说明

---

## 环境变量说明（Northflank控制台粘贴）

```env
TG_API_ID=24812421
TG_API_HASH=63aad0252bfa371ea40cd8b6bfa1e304
TG_PHONE_NUMBER=+8619334015105
TG_LOG_GROUP_ID=-4968047296
BARK_API_KEY=oZaeqGLJzRLSxW7dJqeACn
TG_GROUP_IDS=-1002269920560,-4831222036,-1002700636111,-1001638841860
```
- **TG_API_ID**、**TG_API_HASH**、**TG_PHONE_NUMBER**：你的Telegram API信息
- **TG_LOG_GROUP_ID**：日志群组ID（可选）
- **BARK_API_KEY**：你的Bark推送key（可选）
- **TG_GROUP_IDS**：监听的群组ID，英文逗号分隔

---

## 部署与使用

### 1. 构建并部署到 Northflank
- 直接用 Dockerfile 部署即可。
- 在 Northflank 控制台设置上述环境变量。

### 2. 首次登录 Telegram（SSH 进入容器后执行）
```bash
python -m telethon.sync TelegramClient session_<你的手机号> <api_id> <api_hash>
# 或使用你自己的登录脚本
```
- 按提示输入验证码完成登录。

### 3. 启动监听（SSH 进入容器后执行）
```bash
python main.py
```
- 监听到的消息会直接打印在控制台。
- 检测到"交易"或"signal"关键词会自动推送Bark通知。

---

## 监听多个群组
- 只需在环境变量 TG_GROUP_IDS 中用英文逗号分隔多个群组ID。
- 例如：`TG_GROUP_IDS=-100123,-100456,-100789`

---

## Bark 推送说明
- 配置 BARK_API_KEY 后，监听到交易信号会自动推送到你的 Bark。
- Bark App下载：https://apps.apple.com/cn/app/bark/id1403753865
- Bark官网：https://bark.day.app/

---

## 常见问题
- **环境变量未设置/格式错误**：程序会直接报错并退出。
- **群组ID格式**：必须为英文逗号分隔的纯数字ID。
- **Bark推送失败**：请检查BARK_API_KEY是否正确，或Bark服务可用性。

---

## 适合场景
- 云服务器、Northflank、VPS、Docker等一切支持Python的环境
- 只需监听和推送，无需Web界面和复杂管理

---

如需进一步定制或遇到问题，欢迎联系开发者。 