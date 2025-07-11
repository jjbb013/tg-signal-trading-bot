# Telegram 交易信号监听机器人

一个基于 Telethon 的 Telegram 监听机器人，支持多群组监听、OKX 自动下单、Bark 推送等功能，**现已支持数据持久化存储**。

## 🆕 最新更新 - 数据持久化功能

### 💾 数据持久化特性
- **Session 持久化**: Telegram 登录状态持久化，重启后无需重新登录
- **日志持久化**: 所有日志文件存储在 Northflank Volumes，重启后保留
- **订单数据持久化**: 所有交易订单、信号、盈利数据存储在 SQLite 数据库
- **消息记录持久化**: Telegram 消息和信号检测记录完整保存
- **Web API 接口**: 提供 RESTful API 供 Vercel 等平台调用数据

### 📁 数据存储结构
```
/data/                    # Northflank Volumes 挂载点
├── sessions/            # Telegram Session 文件
│   └── session_xxx.session
├── logs/               # 日志文件
│   ├── tg_bot_2024-01-01.log
│   └── ordered_list.log
├── trading_bot.db      # SQLite 数据库
└── tg_bot.pid          # 进程ID文件
```

### 🌐 API 接口
- `GET /api/health` - 健康检查
- `GET /api/orders` - 查询订单数据
- `GET /api/messages` - 查询消息记录
- `GET /api/statistics` - 查询统计信息
- `GET /api/logs` - 查询日志文件

## 功能特性

### ✅ 已实现功能
- **Telegram 监听**: 支持多群组同时监听交易信号
- **OKX 自动下单**: 支持多账号自动下单，支持做多/做空
- **Bark 推送**: 交易信号和下单结果实时推送
- **日志记录**: 完整的日志记录系统，支持按日期分割
- **订单日志**: 自动记录所有订单信息到 `logs/ordered_list.log`
- **平仓功能**: 支持检测平仓信号并自动平仓
- **定时重启**: 每30分钟自动重启，保持稳定性
- **环境变量配置**: 所有配置通过环境变量注入，适合云平台部署
- **数据持久化**: 所有数据持久化到 Northflank Volumes
- **Web API**: 提供 RESTful API 接口

### 🔄 新增功能 (最新更新)
1. **数据持久化**: Session、日志、订单数据全部持久化存储
2. **SQLite 数据库**: 使用 SQLite 存储订单、消息、日志数据
3. **Web API 服务**: 提供数据查询接口
4. **重启间隔优化**: 从1小时改为30分钟，提高稳定性
5. **订单日志记录**: 每次下单后自动记录详细信息到 `ordered_list.log`
6. **平仓信号检测**: 支持检测"空止盈"、"空止损"、"多止盈"、"多止损"信号
7. **消息合并发送**: 将接收消息和信号检测结果合并为一条消息发送
8. **多账号平仓**: 支持多账号同时平仓操作

## 环境变量配置

### Telegram 配置
```bash
TG_API_ID=你的API_ID
TG_API_HASH=你的API_HASH
TG_PHONE_NUMBER=你的手机号
TG_GROUP_IDS=群组ID1,群组ID2,群组ID3
TG_LOG_GROUP_ID=日志群组ID  # 可选
BARK_API_KEY=你的Bark密钥  # 可选
```

### 数据持久化配置
```bash
DATA_PATH=/data                    # 数据存储路径（Northflank Volumes）
DATABASE_URL=sqlite:////data/trading_bot.db  # 数据库连接
```

### OKX 多账号配置
支持最多5个账号，如需更多可扩展：

```bash
# 账号1
OKX1_API_KEY=账号1的API_KEY
OKX1_SECRET_KEY=账号1的SECRET_KEY
OKX1_PASSPHRASE=账号1的PASSPHRASE
OKX1_LEVERAGE=20
OKX1_FIXED_QTY_ETH=0.1
OKX1_FIXED_QTY_BTC=0.01
OKX1_ACCOUNT_NAME=OKX1
OKX1_FLAG=1

# 账号2
OKX2_API_KEY=账号2的API_KEY
OKX2_SECRET_KEY=账号2的SECRET_KEY
OKX2_PASSPHRASE=账号2的PASSPHRASE
OKX2_LEVERAGE=20
OKX2_FIXED_QTY_ETH=0.1
OKX2_FIXED_QTY_BTC=0.01
OKX2_ACCOUNT_NAME=OKX2
OKX2_FLAG=1

# 继续添加更多账号...
```

## 交易信号格式

### 开仓信号
机器人会检测包含以下格式的消息：
```
执行交易:做多 0.1ETH
策略当前交易对:ETHUSDT.P
```

### 平仓信号
机器人会检测包含以下关键词的消息：
- `空止盈` - 平空头止盈
- `空止损` - 平空头止损  
- `多止盈` - 平多头止盈
- `多止损` - 平多头止损

## 日志文件

- `logs/tg_bot_YYYY-MM-DD.log`: 主日志文件，按日期分割
- `logs/ordered_list.log`: 订单记录文件，记录所有下单信息
- `data/trading_bot.db`: SQLite 数据库，存储所有结构化数据

## 部署说明

### Northflank 部署（推荐）
1. 推送代码到 Git 仓库
2. 在 Northflank 创建新服务
3. 配置环境变量（包括数据持久化配置）
4. 配置 Volumes：挂载 `/data` 目录
5. 设置构建命令和启动命令
6. 部署并启动服务

#### Northflank Volumes 配置
- **卷名称**: `data-volume`
- **挂载路径**: `/data`
- **大小**: 5GB（足够存储所有数据）

#### 启动命令
```bash
python main.py --daemon
```

### Docker 部署
```bash
docker build -t tg-signal-bot .
docker run -d --name tg-bot \
  -v data-volume:/data \
  -e TG_API_ID=你的API_ID \
  -e TG_API_HASH=你的API_HASH \
  -e TG_PHONE_NUMBER=你的手机号 \
  -e TG_GROUP_IDS=群组ID1,群组ID2 \
  -e DATA_PATH=/data \
  -e DATABASE_URL=sqlite:////data/trading_bot.db \
  -e BARK_API_KEY=你的Bark密钥 \
  -e OKX1_API_KEY=账号1的API_KEY \
  -e OKX1_SECRET_KEY=账号1的SECRET_KEY \
  -e OKX1_PASSPHRASE=账号1的PASSPHRASE \
  -e OKX1_LEVERAGE=20 \
  -e OKX1_FIXED_QTY_ETH=0.1 \
  -e OKX1_FIXED_QTY_BTC=0.01 \
  tg-signal-bot
```

## 文件说明

- `main.py`: 主程序文件，使用环境变量配置
- `models.py`: 数据模型定义（新增）
- `database.py`: 数据库管理（新增）
- `api.py`: Web API 服务（新增）
- `auto2h.py`: 升级版程序，使用配置文件
- `login_telegram.py`: Telegram 登录工具
- `Dockerfile`: Docker 构建文件
- `requirements.txt`: Python 依赖包
- `supervisord.conf`: Supervisor 配置文件
- `start.sh`: 启动脚本（新增）
- `check-deployment.sh`: 部署检查脚本（新增）
- `DEPLOYMENT.md`: 详细部署指南（新增）

## 注意事项

1. **首次使用**: 需要先运行 `python main.py --login` 进行 Telegram 登录
2. **数据持久化**: 确保 Northflank Volumes 正确配置，数据存储在 `/data` 目录
3. **API 权限**: 确保 OKX API 有交易权限
4. **资金安全**: 请在小额测试确认无误后再使用大额资金
5. **网络稳定**: 建议部署在稳定的云服务器上
6. **监控日志**: 定期检查日志文件，确保机器人正常运行
7. **数据备份**: 定期备份 `/data` 目录中的重要数据

## 更新日志

### 2024-12-19
- 🆕 **数据持久化**: 支持 Northflank Volumes 数据持久化
- 🆕 **SQLite 数据库**: 使用 SQLite 存储结构化数据
- 🆕 **Web API**: 提供 RESTful API 接口
- 🆕 **Session 持久化**: 重启后无需重新登录 Telegram
- 🆕 **部署脚本**: 新增启动和检查脚本

### 2024-06-29
- ✅ 重启间隔从1小时改为30分钟
- ✅ 新增订单日志记录功能
- ✅ 新增平仓信号检测和自动平仓
- ✅ 优化消息发送，合并接收消息和信号检测
- ✅ 修复 OKX SDK 兼容性问题
- ✅ 完善错误处理和日志记录

### 2024-06-28
- ✅ 初始版本发布
- ✅ 支持多群组监听
- ✅ 支持多账号 OKX 自动下单
- ✅ 支持 Bark 推送
- ✅ 支持环境变量配置 

# 守护进程管理与新增功能

## 新增功能总结

### 🔧 守护进程管理功能
- 启动守护进程: `python main.py --daemon`
- 停止守护进程: `python main.py --stop`
- 查看状态: `python main.py --status`
- 普通模式（前台运行）: `python main.py`

### 📋 主要特性
- **PID文件管理**：自动创建/删除 `tg_bot.pid` 文件，防止多实例冲突
- **进程监控**：可随时检查机器人是否在运行
- **优雅停止**：先发送SIGTERM，10秒后如未退出则强制SIGKILL
- **日志重定向**：守护进程模式下日志输出到 `logs/tg_bot_daemon.log`
- **会话管理**：守护进程独立会话，脱离终端控制

### 🛠️ 使用方式
```bash
# 启动守护进程
python main.py --daemon

# 停止守护进程
python main.py --stop

# 查看守护进程状态
python main.py --status

# 前台普通模式运行
python main.py
```

### 💡 优势
- ✅ 24小时稳定运行：守护进程模式确保机器人持续运行
- ✅ 自动重启：30分钟定时重启，避免内存泄漏
- ✅ 进程管理：支持启动、停止、状态查询
- ✅ 日志分离：守护进程和前台模式日志分开管理
- ✅ 优雅停止：支持信号处理和强制停止

### 🚀 部署后操作
**重要**: 部署完成后，机器人不会自动启动。需要手动SSH连接到实例后启动：

```bash
# 1. SSH连接到Northflank实例
ssh -p <port> <username>@<host>

# 2. 首次运行（需要Telegram登录）
python main.py --login

# 3. 启动守护进程（推荐生产环境）
python main.py --daemon

# 4. 或前台运行（开发测试）
python main.py

# 5. 使用supervisor管理（可选）
./supervisor-manual-start.sh start    # 启动
./supervisor-manual-start.sh stop     # 停止
./supervisor-manual-start.sh status   # 查看状态
./supervisor-manual-start.sh logs     # 查看日志
```

---

现在您的机器人支持完整的守护进程管理，可以在生产环境中稳定运行！所有代码已推送到远程仓库。

--- 