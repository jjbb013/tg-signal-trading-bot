# Telegram 监听机器人（Northflank部署版）

## 功能简介
- 监听多个Telegram群组消息，支持关键词自动Bark推送和OKX自动下单
- 所有配置通过环境变量注入，适合云端/容器部署
- 支持 Northflank 平台一键部署，SSH 登录后手动登录/启动监听
- 代码极简，无Web、无数据库、无代理

---

## 目录结构
- main.py                # 监听主程序（支持Bark推送+OKX自动下单）
- requirements.txt       # 依赖说明
- Dockerfile             # 部署文件
- README.md              # 使用说明
- supervisord.conf       # 进程守护配置

---

## 环境变量说明（Northflank控制台粘贴）

### Telegram配置
- TG_API_ID
- TG_API_HASH
- TG_PHONE_NUMBER
- TG_LOG_GROUP_ID（可选）
- BARK_API_KEY（可选）
- TG_GROUP_IDS（英文逗号分隔多个群组ID）

### OKX账号1
- OKX1_API_KEY
- OKX1_SECRET_KEY
- OKX1_PASSPHRASE
- OKX1_LEVERAGE
- OKX1_FIXED_QTY_ETH
- OKX1_FIXED_QTY_BTC
- OKX1_ACCOUNT_NAME（可选）
- OKX1_FLAG（可选，默认1）

### OKX账号2
- OKX2_API_KEY
- OKX2_SECRET_KEY
- OKX2_PASSPHRASE
- OKX2_LEVERAGE
- OKX2_FIXED_QTY_ETH
- OKX2_FIXED_QTY_BTC
- OKX2_ACCOUNT_NAME（可选）
- OKX2_FLAG（可选，默认1）

---

## 部署与使用

### 1. 构建并部署到 Northflank
- 直接用 Dockerfile 部署即可。
- 在 Northflank 控制台设置上述环境变量。

### 2. 首次登录 Telegram（SSH 进入容器后执行）
```bash
python login_telegram.py
```
- 按提示输入验证码完成登录。

### 3. 启动监听（SSH 进入容器后执行）
```bash
python main.py
```
- 监听到的消息会直接打印在控制台。
- 检测到"交易"或"signal"关键词会自动推送Bark通知并自动下单。

---

## 监听多个群组
- 只需在环境变量 TG_GROUP_IDS 中用英文逗号分隔多个群组ID。
- 例如：`TG_GROUP_IDS=-100123,-100456,-100789`

---

## Bark 推送说明
- 配置 BARK_API_KEY 后，监听到交易信号会自动推送到你的 Bark。

---

## 24小时守护说明
- supervisor 自动后台守护 main.py，监听程序异常退出会自动重启。
- 程序内部自带定时重启机制，防止 Telegram 连接失效。

---

## 其他说明
- 所有敏感信息请勿提交到仓库。
- OKX 相关配置全部通过环境变量注入，无需配置文件。

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