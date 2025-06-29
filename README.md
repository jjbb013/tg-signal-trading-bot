# Telegram 交易信号监听机器人

一个基于 Telethon 的 Telegram 监听机器人，支持多群组监听、OKX 自动下单、Bark 推送等功能。

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

### 🔄 新增功能 (最新更新)
1. **重启间隔优化**: 从1小时改为30分钟，提高稳定性
2. **订单日志记录**: 每次下单后自动记录详细信息到 `ordered_list.log`
3. **平仓信号检测**: 支持检测"空止盈"、"空止损"、"多止盈"、"多止损"信号
4. **消息合并发送**: 将接收消息和信号检测结果合并为一条消息发送
5. **多账号平仓**: 支持多账号同时平仓操作

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

## 部署说明

### Northflank 部署
1. 推送代码到 Git 仓库
2. 在 Northflank 创建新服务
3. 配置环境变量
4. 设置构建命令和启动命令
5. 部署并启动服务

### Docker 部署
```bash
docker build -t tg-signal-bot .
docker run -d --name tg-bot \
  -e TG_API_ID=你的API_ID \
  -e TG_API_HASH=你的API_HASH \
  -e TG_PHONE_NUMBER=你的手机号 \
  -e TG_GROUP_IDS=群组ID1,群组ID2 \
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
- `auto2h.py`: 升级版程序，使用配置文件
- `login_telegram.py`: Telegram 登录工具
- `Dockerfile`: Docker 构建文件
- `requirements.txt`: Python 依赖包
- `supervisord.conf`: Supervisor 配置文件

## 注意事项

1. **首次使用**: 需要先运行 `login_telegram.py` 进行 Telegram 登录
2. **API 权限**: 确保 OKX API 有交易权限
3. **资金安全**: 请在小额测试确认无误后再使用大额资金
4. **网络稳定**: 建议部署在稳定的云服务器上
5. **监控日志**: 定期检查日志文件，确保机器人正常运行

## 更新日志

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