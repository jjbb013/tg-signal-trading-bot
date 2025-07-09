## 🐳 aaPanel Docker 部署指南

1. **拉取代码**
   - 在 aaPanel Docker 管理器中，进入目标目录，执行：
     ```bash
     git clone https://github.com/你的仓库/tg-signal-trading-bot.git
     cd tg-signal-trading-bot
     ```
2. **构建镜像**
   ```bash
   docker build -t tg-signal-bot .
   ```
3. **准备数据卷**
   - 推荐在宿主机创建 `/opt/tg-bot-data` 目录：
     ```bash
     mkdir -p /opt/tg-bot-data
     ```
   - 挂载到容器 `/data`，用于持久化 session、日志、数据库。
4. **准备环境变量**
   - 在 `/opt/tg-bot-data` 下新建 `.env` 文件，内容参考 `.env.example`。
   - 主要变量如：
     ```env
     TG_API_ID=xxxx
     TG_API_HASH=xxxx
     TG_PHONE_NUMBER=xxxx
     TG_GROUP_IDS=xxxx
     OKX1_API_KEY=xxxx
     ...
     DATA_PATH=/data
     ```
5. **启动容器**
   ```bash
   docker run -d --name tg-bot \
     -v /opt/tg-bot-data:/data \
     --env-file /opt/tg-bot-data/.env \
     tg-signal-bot
   ```
6. **守护进程说明**
   - 容器内 supervisor 会自动启动主程序，确保 24 小时运行。
   - 日志、数据库、session 文件都在 `/data` 卷内，方便备份和迁移。

> **注意：**
> - 不需要暴露 API 端口。
> - 所有配置、数据都通过挂载卷和环境变量管理。
> - 支持 web 面板操作（如 aaPanel Docker 管理器），也可用命令行。 