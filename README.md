# Telegram 监听机器人

一个用于监听Telegram群组消息并提取交易信号的机器人。

## 功能特性

- 🤖 实时监听Telegram群组消息
- 📊 自动提取交易信号
- 📱 移动端友好的Web界面
- 🔔 Bark推送通知
- 📝 实时日志和历史日志查询
- 👥 群组管理功能
- 🔄 自动部署支持

## 部署到Northflank

### 1. 准备工作

确保你的项目已经推送到GitHub仓库。

### 2. 在Northflank上部署

1. 登录Northflank控制台
2. 创建新项目
3. 连接GitHub仓库
4. 配置部署设置：
   - **启动命令**: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`
   - **端口**: `8000`
   - **环境变量**: 根据需要设置

### 3. 配置自动部署

#### 方法一：使用Northflank内置的Auto Deploy（推荐）

1. **进入Service设置**
   - 在Northflank控制台中，点击你的Service
   - 进入"Settings"标签页

2. **启用Auto Deploy**
   - 找到"Deployment"部分
   - 启用"Auto Deploy"选项
   - 选择触发分支（通常是`main`）
   - 选择触发条件（推荐选择`Push`）

3. **验证设置**
   - Northflank会自动在你的GitHub仓库中创建webhook
   - 你可以在GitHub仓库的Settings > Webhooks中查看

#### 方法二：使用GitHub Actions

1. **安装Northflank CLI并获取配置信息**
   ```bash
   # 安装CLI
   npm install -g @northflank/cli
   
   # 登录
   northflank auth:login
   
   # 运行配置工具（推荐）
   chmod +x setup-northflank.sh
   ./setup-northflank.sh
   ```

2. **手动获取配置信息（如果脚本不工作）**
   ```bash
   # 获取项目列表
   northflank project:list
   
   # 获取服务列表
   northflank service:list
   
   # 获取API Token
   northflank auth:token
   ```

3. **配置GitHub Secrets**
   - 进入GitHub仓库的Settings > Secrets and variables > Actions
   - 添加以下secrets：
     - `NORTHFLANK_TOKEN`: 从 `northflank auth:token` 获取
     - `NORTHFLANK_PROJECT_ID`: 从项目列表中选择
     - `NORTHFLANK_SERVICE_ID`: 从服务列表中选择

4. **推送代码触发部署**
   - 每次推送到`main`分支时，GitHub Actions会自动触发部署
   - 也可以在GitHub Actions页面手动触发部署

#### 方法三：使用部署脚本

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 4. 配置Telegram API

在Northflank控制台中，通过SSH连接到容器：

```bash
# 连接到容器终端
ssh your-container-ip

# 进入项目目录
cd /app

# 创建配置文件
nano telegram_config.json
```

配置文件内容：
```json
{
    "api_id": "你的API_ID",
    "api_hash": "你的API_HASH", 
    "phone_number": "+8613xxxxxxxxx",
    "bark_api_key": "你的Bark密钥",
    "log_group_id": "日志群组ID"
}
```

### 5. Telegram登录流程

#### 方法一：使用登录脚本（推荐）

```bash
# 在容器终端中运行
python login_telegram.py
```

按照提示操作：
1. 输入手机号（或直接回车使用配置文件中的号码）
2. 输入收到的验证码
3. 如果需要，输入两步验证密码

#### 方法二：手动登录

```bash
# 在容器终端中运行
python -c "
import asyncio
from telethon import TelegramClient
import json

# 加载配置
with open('telegram_config.json', 'r') as f:
    config = json.load(f)

async def login():
    client = TelegramClient(f'session_{config[\"phone_number\"]}', 
                          config['api_id'], config['api_hash'])
    await client.connect()
    
    if not await client.is_user_authorized():
        phone = input('手机号: ')
        await client.send_code_request(phone)
        code = input('验证码: ')
        await client.sign_in(phone, code)
    
    print('登录成功!')
    await client.disconnect()

asyncio.run(login())
"
```

### 6. 启动应用

登录成功后，应用会自动启动。你也可以手动启动：

```bash
# 启动Web界面
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 或者后台运行
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 7. 访问Web界面

在浏览器中访问：`https://your-northflank-domain.com`

## 自动部署工作流

### 开发流程

1. **本地开发**
   ```bash
   # 修改代码
   git add .
   git commit -m "你的修改"
   ```

2. **推送代码**
   ```bash
   git push origin main
   ```

3. **自动部署**
   - 如果配置了Auto Deploy，Northflank会自动检测并部署
   - 如果使用GitHub Actions，会在Actions中看到部署进度
   - 如果使用部署脚本，会显示部署状态

### 部署状态检查

- **Northflank控制台**: 查看部署历史和状态
- **GitHub Actions**: 查看部署日志和错误信息
- **应用日志**: 检查应用是否正常运行

## 使用说明

### Web界面功能

1. **🤖 机器人状态** - 查看运行状态和Session状态
2. **📝 实时日志** - 查看实时监听日志
3. **📋 日志查询** - 查询历史日志文件
4. **👥 监听群组** - 管理监听的群组
5. **📱 配置信息** - 修改API配置

### 添加监听群组

1. 在Telegram中获取群组ID
2. 在Web界面的"监听群组"区域添加群组ID
3. 群组ID通常是负数，如：`-1001234567890`

### 获取Telegram API

1. 访问 https://my.telegram.org
2. 登录你的Telegram账号
3. 创建新应用
4. 获取 `api_id` 和 `api_hash`

## 故障排除

### Session失效

如果Session失效，重新登录：

```bash
# 删除旧的session文件
rm session_*.session*

# 重新运行登录脚本
python login_telegram.py
```

### 网络连接问题

确保容器能够访问Telegram服务器。如果在中国大陆，可能需要配置代理。

### 权限问题

确保应用有足够的权限访问文件系统：

```bash
# 检查文件权限
ls -la

# 修改权限
chmod 755 *.py
chmod 644 *.json
```

### 自动部署问题

如果自动部署失败：

1. **检查GitHub Webhook**
   - 进入GitHub仓库的Settings > Webhooks
   - 查看webhook是否正常

2. **检查Northflank设置**
   - 确认Auto Deploy已启用
   - 检查分支配置是否正确

3. **查看部署日志**
   - 在Northflank控制台查看部署历史
   - 检查错误信息

## 文件结构

```
tg-signal-trading-bot/
├── main.py              # FastAPI主应用
├── bot.py               # Telegram机器人逻辑
├── models.py            # 数据库模型
├── database.py          # 数据库配置
├── login_telegram.py    # Telegram登录脚本
├── start.sh             # 启动脚本
├── deploy.sh            # 部署脚本
├── telegram_config.json # 配置文件
├── requirements.txt     # Python依赖
├── Dockerfile          # Docker配置
├── .github/workflows/   # GitHub Actions
│   └── deploy.yml
├── static/             # 静态文件
│   └── main.css
└── templates/          # HTML模板
    └── index.html
```

## 注意事项

1. **安全性**: 不要将 `telegram_config.json` 提交到公开仓库
2. **Session文件**: 登录成功后会在当前目录生成session文件，请妥善保管
3. **API限制**: 注意Telegram API的使用限制
4. **隐私**: 确保遵守相关法律法规和隐私政策
5. **自动部署**: 确保生产环境的配置正确，避免自动部署导致的问题

## 技术支持

如果遇到问题，请检查：
1. 配置文件是否正确
2. 网络连接是否正常
3. Session是否有效
4. 日志文件中的错误信息
5. 自动部署配置是否正确 