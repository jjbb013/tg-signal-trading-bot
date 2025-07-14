# Northflank 部署说明

本目录为适配 Northflank 云平台的 Telegram 信号机器人部署包。

## 目录结构
- `tgBotV2.py`         主程序
- `utils.py`          工具函数
- `requirements.txt`  依赖包
- `start.sh`          启动脚本
- `supervisord.conf`  进程管理
- `Dockerfile`        构建镜像
- `project_log.md`    功能与风格规范
- `processed_message_ids.json`  消息去重缓存（需持久化）
- `data/sessions/`    Telegram 登录 session（需持久化）

## Northflank 部署要点

### 1. 数据持久化
- **所有需持久化的文件（如 `data/sessions/`、`processed_message_ids.json`）请挂载到 Northflank 的 Volume：`tg-listen-data`**
- 推荐挂载点：
  - `/app/data/sessions`  ←→  `tg-listen-data/data/sessions`
  - `/app/processed_message_ids.json`  ←→  `tg-listen-data/processed_message_ids.json`
  - `/app/logs`  ←→  `tg-listen-data/logs`（如需日志持久化）

### 2. 环境变量
- 所有敏感信息、参数（如 API KEY、杠杆倍数、频道ID、定时参数等）均通过 Northflank 环境变量注入。
- 支持的主要环境变量：
  - `TG_API_ID`、`TG_API_HASH`、`TG_LOG_GROUP_ID`、`TG_CHANNEL_IDS`
  - `OKX1_API_KEY`、`OKX1_SECRET_KEY`、`OKX1_PASSPHRASE`、`OKX1_FLAG` ...
  - `OKX1_LEVERAGE`、`OKX2_LEVERAGE` ...
  - `AUTO_RESTART_INTERVAL`、`PATCH_MISSING_SIGNALS_INTERVAL`

### 3. Dockerfile 说明
- 已适配 Northflank，工作目录为 `/app`，所有持久化数据建议挂载到 `/app` 下对应路径。

### 4. 启动命令
- 推荐使用 `start.sh` 脚本启动（自动创建目录并启动 supervisor）：
  ```sh
  bash start.sh
  ```
- 或直接用 supervisor：
  ```sh
  supervisord -c supervisord.conf
  ```

### 5. 典型 Northflank Volume 挂载示例
- `tg-listen-data:/app/data/sessions`
- `tg-listen-data:/app/processed_message_ids.json`
- `tg-listen-data:/app/logs`

---

如需自定义挂载点或环境变量，请根据 Northflank 平台实际配置调整。

详细功能、日志格式、风格规范请见 `project_log.md`。 