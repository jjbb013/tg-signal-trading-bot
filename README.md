# Telegram 极简监听机器人

## 功能
- 只保留 Telegram 群组监听与消息打印
- 无Web、无数据库、无Bark、无代理
- 支持SSH登录 Northflank 容器后手动登录和启动监听

## 使用方法

### 1. 配置参数
编辑 `telegram_config.json`：
```json
{
  "api_id": "你的API_ID",
  "api_hash": "你的API_HASH",
  "phone_number": "你的手机号",
  "log_group_id": "你的日志群组ID"
}
```

### 2. 构建并部署到 Northflank
- 直接用 Dockerfile 部署即可。

### 3. 首次登录 Telegram（SSH 进入容器后执行）
```bash
python login_telegram.py
```
按提示输入验证码完成登录。

### 4. 编辑监听群组
- 编辑 `main.py` 里的 `group_ids` 列表，填入你要监听的群组ID。

### 5. 启动监听（SSH 进入容器后执行）
```bash
python main.py
```

监听到的消息会直接打印在控制台。

---

## 目录结构
- main.py                # 监听主程序
- login_telegram.py      # 首次登录脚本
- telegram_config.json   # 配置文件
- requirements.txt       # 依赖
- Dockerfile             # 部署文件
- README.md              # 使用说明

---

如需添加监听群组，只需修改 `main.py` 里的 `group_ids`。 