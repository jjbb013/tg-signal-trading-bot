# Telegram Trading Bot 部署文档

## 项目概述

这是一个基于Telethon的Telegram交易信号监听机器人，支持：
- 自动监听Telegram群组消息
- 提取交易信号（做多/做空/平仓）
- 自动下单到OKX交易所
- 数据持久化存储（Session、日志、订单历史）
- Web API接口供Vercel调用

## 目录结构

```
tg-signal-trading-bot/
├── main.py              # 主程序（机器人核心逻辑）
├── api.py               # Web API服务
├── models.py            # 数据模型定义
├── database.py          # 数据库管理
├── requirements.txt     # Python依赖
├── Dockerfile           # Docker配置
├── supervisord.conf     # 进程管理配置
├── DEPLOYMENT.md        # 部署文档
└── README.md           # 项目说明
```

## 数据持久化架构

### 存储路径
所有数据都存储在 `/data` 目录（Northflank Volumes）：
```
/data/
├── sessions/           # Telegram Session文件
│   └── session_xxx.session
├── logs/              # 日志文件
│   ├── tg_bot_2024-01-01.log
│   ├── tg_bot_2024-01-02.log
│   └── ordered_list.log
└── trading_bot.db     # SQLite数据库
```

### 数据表结构
- `trading_orders`: 交易订单记录
- `telegram_messages`: Telegram消息记录
- `system_logs`: 系统日志
- `bot_sessions`: 机器人会话状态

## 环境变量配置

### 必需环境变量
```bash
# Telegram配置
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE_NUMBER=+8613800138000
TG_GROUP_IDS=-1001234567890,-1001234567891

# 数据存储路径（Northflank部署时设为/data）
DATA_PATH=/data
```

### 可选环境变量
```bash
# 日志群组（用于发送通知）
TG_LOG_GROUP_ID=-1001234567892

# Bark推送通知
BARK_API_KEY=your_bark_api_key

# OKX交易所配置（支持多账号）
OKX1_API_KEY=your_okx1_api_key
OKX1_SECRET_KEY=your_okx1_secret_key
OKX1_PASSPHRASE=your_okx1_passphrase
OKX1_LEVERAGE=10
OKX1_FIXED_QTY_ETH=0.01
OKX1_FIXED_QTY_BTC=0.001
OKX1_ACCOUNT_NAME=OKX1
OKX1_FLAG=1

# 可以配置多个OKX账号（OKX2_, OKX3_...）
OKX2_API_KEY=your_okx2_api_key
# ... 其他配置
```

## 本地开发部署

### 1. 环境准备
```bash
# 克隆项目
git clone https://github.com/your-username/tg-signal-trading-bot.git
cd tg-signal-trading-bot

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，填入您的配置
nano .env
```

### 3. 首次登录Telegram
```bash
# 运行登录命令
python main.py --login

# 按照提示输入验证码
# Session文件将保存到 ./data/sessions/session_xxx.session
```

### 4. 启动机器人
```bash
# 普通模式启动
python main.py

# 守护进程模式启动
python main.py --daemon

# 启动Web API服务
python api.py
```

### 5. 管理机器人
```bash
# 检查状态
python main.py --status

# 停止机器人
python main.py --stop
```

## Northflank 部署

### 1. 准备部署文件

确保以下文件已准备好：
- `Dockerfile`
- `requirements.txt`
- `supervisord.conf`
- 所有Python源代码文件

### 2. 在Northflank创建项目

1. 登录Northflank控制台
2. 创建新项目
3. 选择"从Git仓库部署"
4. 连接您的GitHub仓库

### 3. 配置环境变量

在Northflank项目设置中添加以下环境变量：

```bash
# 数据存储路径（重要！）
DATA_PATH=/data

# Telegram配置
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE_NUMBER=+8613800138000
TG_GROUP_IDS=-1001234567890,-1001234567891

# 可选配置
TG_LOG_GROUP_ID=-1001234567892
BARK_API_KEY=your_bark_api_key

# OKX配置
OKX1_API_KEY=your_okx1_api_key
OKX1_SECRET_KEY=your_okx1_secret_key
OKX1_PASSPHRASE=your_okx1_passphrase
OKX1_LEVERAGE=10
OKX1_FIXED_QTY_ETH=0.01
OKX1_FIXED_QTY_BTC=0.001
OKX1_ACCOUNT_NAME=OKX1
OKX1_FLAG=1
```

### 4. 配置Volumes

1. 在Northflank项目设置中找到"Volumes"
2. 添加新的Volume：
   - **名称**: `data`
   - **路径**: `/data`
   - **大小**: 5GB（足够存储所有数据）

### 5. 配置启动命令

在Northflank项目设置中设置启动命令：
```bash
supervisord -c /app/supervisord.conf
```

### 6. 部署

1. 点击"部署"按钮
2. 等待构建完成
3. 检查部署状态

### 7. 首次登录

部署完成后，需要通过SSH连接到容器进行首次Telegram登录：

```bash
# 通过Northflank控制台SSH连接到容器
ssh your-project-name@your-northflank-domain.com

# 在容器内运行登录命令
python main.py --login

# 按照提示输入验证码
# Session文件将保存到 /data/sessions/session_xxx.session
```

### 8. 验证部署

检查以下内容：
- 机器人是否正常运行
- 日志文件是否正常生成
- API接口是否可访问

## API接口文档

### 基础信息
- **基础URL**: `https://your-northflank-domain.com`
- **API版本**: v1.0.0

### 接口列表

#### 1. 健康检查
```http
GET /api/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database": "connected",
  "file_manager": "ready"
}
```

#### 2. 获取交易订单
```http
GET /api/orders?limit=100&offset=0&account_name=OKX1&symbol=ETH&start_date=2024-01-01&end_date=2024-01-31
```

**参数说明**:
- `limit`: 返回数量限制（1-1000）
- `offset`: 偏移量
- `account_name`: 账号名称过滤
- `symbol`: 交易对过滤
- `start_date`: 开始日期（ISO格式）
- `end_date`: 结束日期（ISO格式）

#### 3. 获取Telegram消息
```http
GET /api/messages?limit=100&offset=0&group_id=-1001234567890&has_signal=true
```

**参数说明**:
- `limit`: 返回数量限制（1-1000）
- `offset`: 偏移量
- `group_id`: 群组ID过滤
- `has_signal`: 是否有交易信号

#### 4. 获取交易统计
```http
GET /api/statistics?start_date=2024-01-01&end_date=2024-01-31
```

**响应示例**:
```json
{
  "total_orders": 150,
  "successful_orders": 145,
  "failed_orders": 5,
  "success_rate": 96.67,
  "total_profit_loss": 1250.50,
  "period": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59"
  }
}
```

#### 5. 获取系统日志
```http
GET /api/logs?date=2024-01-01&lines=100
```

**参数说明**:
- `date`: 日志日期（YYYY-MM-DD格式）
- `lines`: 返回行数（1-1000）

#### 6. 获取可用日志日期
```http
GET /api/logs/dates
```

**响应示例**:
```json
{
  "available_dates": ["2024-01-01", "2024-01-02", "2024-01-03"]
}
```

#### 7. 获取订单摘要统计
```http
GET /api/orders/summary?days=7
```

**参数说明**:
- `days`: 统计天数（1-365）

## Vercel集成

### 1. 创建Vercel项目

1. 登录Vercel
2. 创建新项目
3. 选择"从Git仓库导入"

### 2. 配置环境变量

在Vercel项目设置中添加：
```bash
API_BASE_URL=https://your-northflank-domain.com
```

### 3. 前端代码示例

```javascript
// 获取交易订单
async function getOrders() {
  const response = await fetch(`${process.env.API_BASE_URL}/api/orders?limit=50`);
  const orders = await response.json();
  return orders;
}

// 获取交易统计
async function getStatistics() {
  const response = await fetch(`${process.env.API_BASE_URL}/api/statistics`);
  const stats = await response.json();
  return stats;
}

// 获取系统日志
async function getLogs(date) {
  const response = await fetch(`${process.env.API_BASE_URL}/api/logs?date=${date}&lines=100`);
  const logs = await response.json();
  return logs;
}
```

## 监控和维护

### 1. 日志监控

通过API接口监控系统状态：
```bash
# 检查健康状态
curl https://your-northflank-domain.com/api/health

# 查看最新日志
curl https://your-northflank-domain.com/api/logs?lines=50
```

### 2. 数据备份

Northflank Volumes会自动备份，但建议定期导出重要数据：
```bash
# 导出数据库
sqlite3 /data/trading_bot.db ".backup /data/backup_$(date +%Y%m%d).db"

# 导出日志文件
tar -czf /data/logs_backup_$(date +%Y%m%d).tar.gz /data/logs/
```

### 3. 性能优化

- 定期清理旧日志文件
- 监控数据库大小
- 检查API响应时间

## 故障排除

### 常见问题

#### 1. Session文件丢失
**症状**: 机器人提示需要重新登录
**解决**: 重新运行 `python main.py --login`

#### 2. 数据库连接失败
**症状**: API返回500错误
**解决**: 检查 `/data` 目录权限，确保数据库文件可写

#### 3. 日志文件无法写入
**症状**: 程序启动失败
**解决**: 检查 `/data/logs` 目录权限

#### 4. API接口无响应
**症状**: Vercel无法获取数据
**解决**: 检查Northflank服务状态，确认API服务正常运行

### 调试命令

```bash
# 检查容器状态
docker ps

# 查看容器日志
docker logs your-container-name

# 进入容器调试
docker exec -it your-container-name /bin/bash

# 检查数据目录
ls -la /data/
ls -la /data/sessions/
ls -la /data/logs/
```

## 安全注意事项

1. **API密钥安全**: 不要在代码中硬编码API密钥
2. **环境变量**: 使用环境变量管理敏感信息
3. **访问控制**: 考虑为API添加认证机制
4. **数据备份**: 定期备份重要数据
5. **监控告警**: 设置异常监控和告警

## 更新和升级

### 1. 代码更新
```bash
# 拉取最新代码
git pull origin main

# 重新部署到Northflank
# 通过GitHub自动触发部署
```

### 2. 依赖更新
```bash
# 更新requirements.txt
pip freeze > requirements.txt

# 提交并推送
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 3. 数据库迁移
如果数据模型有变更，需要执行数据库迁移：
```bash
# 备份现有数据
cp /data/trading_bot.db /data/trading_bot_backup.db

# 重新创建表（会丢失数据）
python -c "from models import create_tables; create_tables()"
```

## 联系和支持

如果您在部署过程中遇到问题，请：

1. 查看项目日志
2. 检查环境变量配置
3. 确认Northflank服务状态
4. 查看API健康检查接口

---

**注意**: 本部署文档假设您已经在Northflank上配置了正确的环境变量和Volumes。请根据实际情况调整配置参数。

# Northflank 部署指南

## 概述

本指南将帮助您在 Northflank 上部署 Telegram 交易机器人，并配置数据持久化存储。

## 部署前准备

### 1. 环境变量配置

在 Northflank 项目设置中配置以下环境变量：

#### Telegram 配置
```
TG_API_ID=你的Telegram_API_ID
TG_API_HASH=你的Telegram_API_HASH
TG_PHONE_NUMBER=你的手机号码
TG_GROUP_IDS=群组ID1,群组ID2,群组ID3
TG_LOG_GROUP_ID=日志群组ID（可选）
BARK_API_KEY=Bark推送密钥（可选）
```

#### OKX 交易配置（支持多账号）
```
OKX1_API_KEY=账号1_API_KEY
OKX1_SECRET_KEY=账号1_SECRET_KEY
OKX1_PASSPHRASE=账号1_PASSPHRASE
OKX1_LEVERAGE=20
OKX1_FIXED_QTY_ETH=0.01
OKX1_FIXED_QTY_BTC=0.001
OKX1_ACCOUNT_NAME=OKX1
OKX1_FLAG=1

OKX2_API_KEY=账号2_API_KEY
OKX2_SECRET_KEY=账号2_SECRET_KEY
OKX2_PASSPHRASE=账号2_PASSPHRASE
OKX2_LEVERAGE=20
OKX2_FIXED_QTY_ETH=0.01
OKX2_FIXED_QTY_BTC=0.001
OKX2_ACCOUNT_NAME=OKX2
OKX2_FLAG=1
```

#### 数据存储配置
```
DATA_PATH=/data
DATABASE_URL=sqlite:////data/trading_bot.db
```

### 2. Volumes 配置

在 Northflank 中配置持久化存储卷：

- **卷名称**: `data-volume`
- **挂载路径**: `/data`
- **大小**: 5GB（足够存储所有数据）

## 部署步骤

### 1. 创建 Northflank 项目

1. 登录 Northflank 控制台
2. 创建新项目
3. 选择 "Deploy from Git" 或 "Deploy from Image"

### 2. 配置构建设置

#### 如果使用 Git 部署：
- **仓库**: 您的 GitHub 仓库地址
- **分支**: `main` 或 `master`
- **构建命令**: `docker build -t tg-bot .`
- **启动命令**: `python main.py --daemon`

#### 如果使用 Docker 镜像：
- **镜像**: `your-registry/tg-bot:latest`
- **启动命令**: `python main.py --daemon`

### 3. 配置服务设置

#### 端口配置
- **端口**: 8000（API服务）
- **协议**: HTTP

#### 资源限制
- **CPU**: 0.5-1.0 核
- **内存**: 512MB-1GB
- **存储**: 5GB（通过Volumes）

### 4. 挂载 Volumes

在服务配置中添加卷挂载：
- **卷名称**: `data-volume`
- **容器路径**: `/data`
- **权限**: 读写

### 5. 部署和启动

1. 点击 "Deploy" 开始部署
2. 等待构建完成
3. 检查服务状态

## 首次登录配置

### 1. 检查服务状态

部署完成后，首先检查服务是否正常运行：

```bash
# 查看服务日志
northflank logs your-service-name

# 检查健康状态
curl https://your-service.northflank.app/api/health
```

### 2. 执行 Telegram 登录

由于是首次运行，需要登录 Telegram：

```bash
# 进入容器执行登录
northflank exec your-service-name -- python main.py --login
```

或者通过 Web 终端：

1. 在 Northflank 控制台打开 Web 终端
2. 执行：`python main.py --login`
3. 按照提示输入手机号和验证码

### 3. 启动机器人

登录成功后，启动机器人：

```bash
# 启动守护进程
northflank exec your-service-name -- python main.py --daemon
```

## 数据持久化验证

### 1. 检查数据目录

```bash
# 进入容器检查数据目录
northflank exec your-service-name -- ls -la /data/

# 应该看到以下目录和文件：
# sessions/     - Telegram session 文件
# logs/         - 日志文件
# trading_bot.db - SQLite 数据库
# tg_bot.pid    - 进程ID文件
```

### 2. 验证 Session 文件

```bash
# 检查 session 文件是否存在
northflank exec your-service-name -- ls -la /data/sessions/

# 应该看到类似文件：
# session_+8613764176027.session
```

### 3. 验证数据库

```bash
# 检查数据库文件
northflank exec your-service-name -- ls -la /data/trading_bot.db

# 测试数据库连接
northflank exec your-service-name -- python -c "
from models import SessionLocal
db = SessionLocal()
print('数据库连接成功')
db.close()
"
```

## API 接口测试

### 1. 健康检查

```bash
curl https://your-service.northflank.app/api/health
```

预期响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database": "connected",
  "file_manager": "ready"
}
```

### 2. 查询订单数据

```bash
curl "https://your-service.northflank.app/api/orders?limit=10"
```

### 3. 查询统计信息

```bash
curl "https://your-service.northflank.app/api/statistics"
```

### 4. 查询日志

```bash
curl "https://your-service.northflank.app/api/logs?date=2024-01-01&lines=50"
```

## 监控和维护

### 1. 日志监控

```bash
# 查看实时日志
northflank logs your-service-name -f

# 查看特定日期的日志
northflank exec your-service-name -- cat /data/logs/tg_bot_2024-01-01.log
```

### 2. 数据库备份

```bash
# 备份数据库
northflank exec your-service-name -- cp /data/trading_bot.db /data/trading_bot_backup.db

# 从备份恢复
northflank exec your-service-name -- cp /data/trading_bot_backup.db /data/trading_bot.db
```

### 3. 服务重启

```bash
# 停止服务
northflank exec your-service-name -- python main.py --stop

# 启动服务
northflank exec your-service-name -- python main.py --daemon
```

## 故障排除

### 1. 常见问题

#### Session 文件丢失
```bash
# 重新登录
northflank exec your-service-name -- python main.py --login
```

#### 数据库损坏
```bash
# 备份当前数据库
northflank exec your-service-name -- cp /data/trading_bot.db /data/trading_bot_backup.db

# 重新创建表（会丢失数据）
northflank exec your-service-name -- python -c "from models import create_tables; create_tables()"
```

#### 权限问题
```bash
# 检查目录权限
northflank exec your-service-name -- ls -la /data/

# 修复权限
northflank exec your-service-name -- chmod -R 755 /data/
```

### 2. 日志分析

```bash
# 查看错误日志
northflank logs your-service-name | grep ERROR

# 查看系统日志
northflank exec your-service-name -- tail -f /data/logs/tg_bot_$(date +%Y-%m-%d).log
```

## 性能优化

### 1. 资源调整

根据实际使用情况调整：
- **CPU**: 0.5-2.0 核
- **内存**: 512MB-2GB
- **存储**: 5GB-10GB

### 2. 数据库优化

```bash
# 清理旧日志
northflank exec your-service-name -- find /data/logs -name "*.log" -mtime +30 -delete

# 数据库压缩
northflank exec your-service-name -- sqlite3 /data/trading_bot.db "VACUUM;"
```

## 安全建议

### 1. 环境变量安全
- 使用强密码
- 定期轮换API密钥
- 限制API访问权限

### 2. 网络安全
- 配置防火墙规则
- 使用HTTPS
- 限制API访问来源

### 3. 数据安全
- 定期备份数据
- 加密敏感信息
- 监控异常访问

## 联系和支持

如果您在部署过程中遇到问题，请：

1. 查看项目日志
2. 检查环境变量配置
3. 确认Northflank服务状态
4. 查看API健康检查接口

---

**注意**: 本部署文档假设您已经在Northflank上配置了正确的环境变量和Volumes。请根据实际情况调整配置参数。

## 数据库权限问题解决方案

在 Northflank 部署时，可能会遇到 SQLite 数据库文件无法打开的错误：

```
sqlite3.OperationalError: unable to open database file
```

### 问题原因

这个错误通常是由于以下原因造成的：

1. 数据库目录不存在
2. 数据库目录权限不足
3. 容器用户没有写入权限

### 解决方案

#### 方案1：使用环境变量配置数据库路径

在 Northflank 的环境变量中设置：

```
DATA_PATH=/data
DATABASE_URL=sqlite:////data/trading_bot.db
```

#### 方案2：确保数据卷挂载正确

在 Northflank 配置中，确保数据卷正确挂载到 `/data` 目录。

#### 方案3：手动创建数据库目录

如果问题仍然存在，可以在容器启动时手动创建目录：

```bash
# 进入容器
kubectl exec -it <pod-name> -- /bin/bash

# 创建目录并设置权限
mkdir -p /data/sessions /data/logs
chmod 755 /data /data/sessions /data/logs
chown -R 1000:1000 /data  # 如果使用非root用户
```

#### 方案4：使用内存数据库（临时解决方案）

如果只是为了测试，可以临时使用内存数据库：

```
DATABASE_URL=sqlite:///:memory:
```

### 验证步骤

1. 检查目录是否存在：
   ```bash
   ls -la /data/
   ```

2. 检查权限：
   ```bash
   ls -la /data/trading_bot.db
   ```

3. 测试数据库连接：
   ```bash
   python -c "from models import engine; print('数据库连接成功')"
   ```

### 常见问题

#### Q: 为什么会出现权限问题？
A: 在容器环境中，默认用户可能没有对挂载卷的写入权限。

#### Q: 如何永久解决权限问题？
A: 在 Dockerfile 中创建目录并设置正确的权限，或者使用 init 容器来设置权限。

#### Q: 可以使用其他数据库吗？
A: 是的，可以修改 `DATABASE_URL` 环境变量来使用 PostgreSQL 或 MySQL。

### 环境变量配置

确保以下环境变量正确设置：

```bash
# 必需的环境变量
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE_NUMBER=your_phone_number
TG_GROUP_IDS=group_id1,group_id2

# 数据路径配置
DATA_PATH=/data
DATABASE_URL=sqlite:////data/trading_bot.db

# OKX 配置（可选）
OKX1_API_KEY=your_api_key
OKX1_SECRET_KEY=your_secret_key
OKX1_PASSPHRASE=your_passphrase
OKX1_LEVERAGE=10
OKX1_FIXED_QTY_ETH=0.01
OKX1_FIXED_QTY_BTC=0.001
OKX1_ACCOUNT_NAME=OKX1
OKX1_FLAG=1
```

### 故障排除

如果仍然遇到问题，请检查：

1. 容器日志：
   ```bash
   kubectl logs <pod-name>
   ```

2. 文件系统权限：
   ```bash
   kubectl exec -it <pod-name> -- ls -la /data/
   ```

3. 数据库文件状态：
   ```bash
   kubectl exec -it <pod-name> -- python -c "import sqlite3; sqlite3.connect('/data/trading_bot.db')"
   ``` 