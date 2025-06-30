import asyncio
from telethon.sync import TelegramClient
import requests
from telethon import events
import re
from datetime import datetime, timedelta
import pytz
import os
import okx.Trade as Trade
import okx.MarketData as MarketData
import okx.Account as Account
import random
import logging
import traceback
import time
import threading
import sys
import json
import subprocess
import signal
import argparse

# 导入数据持久化模块
from models import create_tables
from database import DatabaseManager, FileManager

# 数据路径配置 - 支持Northflank Volumes
DATA_PATH = os.getenv('DATA_PATH', '/data')  # Northflank Volumes 映射到 /data
SESSION_PATH = os.path.join(DATA_PATH, 'sessions')
LOGS_PATH = os.path.join(DATA_PATH, 'logs')
DB_PATH = os.path.join(DATA_PATH, 'trading_bot.db')

# 确保目录存在并设置权限
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(SESSION_PATH, exist_ok=True)
os.makedirs(LOGS_PATH, exist_ok=True)

# 设置目录权限
try:
    os.chmod(DATA_PATH, 0o755)
    os.chmod(SESSION_PATH, 0o755)
    os.chmod(LOGS_PATH, 0o755)
except Exception as e:
    print(f"设置目录权限失败: {e}")

# 设置数据库环境变量
os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH}'

# 初始化数据持久化 - 使用Northflank Volumes路径
try:
    create_tables()
    print("数据库表创建成功")
except Exception as e:
    print(f"数据库表创建失败: {e}")
    print(f"数据库路径: {DB_PATH}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"数据目录权限: {oct(os.stat(DATA_PATH).st_mode)[-3:]}")
    sys.exit(1)

file_manager = FileManager(DATA_PATH)

# 日志设置
def setup_logger():
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = os.path.join(LOGS_PATH, f'tg_bot_{current_date}.log')
    logger = logging.getLogger('tg_bot')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# 环境变量读取
def get_env(name, required=True):
    value = os.getenv(name)
    if required and not value:
        logger.error(f"[FATAL] 缺少环境变量: {name}")
        sys.exit(1)
    return value

# Telegram配置
TG_API_ID = get_env('TG_API_ID')
if TG_API_ID is None or TG_API_ID == '':
    logger.error("[FATAL] TG_API_ID 必须设置且为整数")
    sys.exit(1)
try:
    TG_API_ID = int(TG_API_ID)
except Exception:
    logger.error("[FATAL] TG_API_ID 必须为整数")
    sys.exit(1)
TG_API_HASH = get_env('TG_API_HASH')
if TG_API_HASH is None or TG_API_HASH == '':
    logger.error("[FATAL] TG_API_HASH 必须设置")
    sys.exit(1)
TG_PHONE_NUMBER = get_env('TG_PHONE_NUMBER')
TG_LOG_GROUP_ID = get_env('TG_LOG_GROUP_ID', required=False)
if TG_LOG_GROUP_ID is not None and TG_LOG_GROUP_ID != '':
    try:
        TG_LOG_GROUP_ID = int(TG_LOG_GROUP_ID)
    except Exception:
        logger.error("[FATAL] TG_LOG_GROUP_ID 必须为整数")
        sys.exit(1)
else:
    TG_LOG_GROUP_ID = None
BARK_API_KEY = get_env('BARK_API_KEY', required=False)
TG_GROUP_IDS_ENV = get_env('TG_GROUP_IDS') or ''
try:
    TG_GROUP_IDS = [int(gid.strip()) for gid in TG_GROUP_IDS_ENV.split(',') if gid.strip()]
except Exception:
    logger.error("[FATAL] TG_GROUP_IDS 格式错误，必须为英文逗号分隔的群组ID列表")
    sys.exit(1)
if not TG_GROUP_IDS:
    logger.error("[FATAL] TG_GROUP_IDS 未配置监听群组ID，或内容为空")
    sys.exit(1)

# Session文件路径 - 使用Northflank Volumes
SESSION_NAME = f'session_{TG_PHONE_NUMBER}'
SESSION_FILE = os.path.join(SESSION_PATH, f'{SESSION_NAME}.session')

# OKX多账号配置
OKX_ACCOUNTS = []
for idx in range(1, 6):
    prefix = f'OKX{idx}_'
    api_key = get_env(prefix + 'API_KEY', required=False)
    secret_key = get_env(prefix + 'SECRET_KEY', required=False)
    passphrase = get_env(prefix + 'PASSPHRASE', required=False)
    leverage = get_env(prefix + 'LEVERAGE', required=False)
    fixed_qty_eth = get_env(prefix + 'FIXED_QTY_ETH', required=False)
    fixed_qty_btc = get_env(prefix + 'FIXED_QTY_BTC', required=False)
    account_name = get_env(prefix + 'ACCOUNT_NAME', required=False) or f'OKX{idx}'
    flag = get_env(prefix + 'FLAG', required=False) or '1'
    if api_key and secret_key and passphrase and leverage and fixed_qty_eth and fixed_qty_btc:
        OKX_ACCOUNTS.append({
            'account_name': account_name,
            'API_KEY': api_key,
            'SECRET_KEY': secret_key,
            'PASSPHRASE': passphrase,
            'LEVERAGE': int(leverage),
            'FIXED_QTY': {'ETH': fixed_qty_eth, 'BTC': fixed_qty_btc},
            'FLAG': flag
        })

if not OKX_ACCOUNTS:
    logger.warning("未检测到任何OKX账号环境变量，自动下单功能将不可用。")

# 订单日志记录 - 使用数据库和文件双重记录
def log_order_to_database(order_info):
    """将订单信息记录到数据库"""
    try:
        with DatabaseManager() as db:
            db.add_trading_order(order_info)
        logger.info("订单信息已记录到数据库")
    except Exception as e:
        logger.error(f"记录订单信息到数据库失败: {e}")
        logger.error(traceback.format_exc())

def log_order_to_file(order_info):
    """将订单信息记录到文件"""
    try:
        file_manager.write_order_log(order_info)
        logger.info("订单信息已记录到文件")
    except Exception as e:
        logger.error(f"记录订单信息到文件失败: {e}")

def log_order(order_info):
    """记录订单信息到数据库和文件"""
    log_order_to_database(order_info)
    log_order_to_file(order_info)

def log_telegram_message(message_data):
    """记录Telegram消息到数据库"""
    try:
        with DatabaseManager() as db:
            db.add_telegram_message(message_data)
    except Exception as e:
        logger.error(f"记录Telegram消息失败: {e}")

def log_system_message(level, module, message):
    """记录系统消息到数据库"""
    try:
        with DatabaseManager() as db:
            db.add_system_log(level, module, message)
    except Exception as e:
        logger.error(f"记录系统消息失败: {e}")

# Bark 推送
def send_bark_notification(bark_api_key, title, message):
    if not bark_api_key:
        return False
    bark_url = f"https://api.day.app/{bark_api_key}/"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'title': title,
        'body': message,
        'group': 'TG Signal',
    }
    try:
        response = requests.post(bark_url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"Bark 通知发送成功: {title}")
            return True
        else:
            logger.warning(f"Bark 通知发送失败, 状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"发送 Bark 通知时出错: {e}")
        logger.error(traceback.format_exc())
        return False

# 提取交易信息
def extract_trade_info(message):
    logger.debug(f"正在从消息中提取交易信息: {message[:100]}...")
    
    # 做多信号
    long_patterns = [
        r'做多\s*([A-Z]+)',
        r'([A-Z]+)\s*做多',
        r'买入\s*([A-Z]+)',
        r'([A-Z]+)\s*买入',
        r'LONG\s*([A-Z]+)',
        r'([A-Z]+)\s*LONG'
    ]
    
    # 做空信号
    short_patterns = [
        r'做空\s*([A-Z]+)',
        r'([A-Z]+)\s*做空',
        r'卖出\s*([A-Z]+)',
        r'([A-Z]+)\s*卖出',
        r'SHORT\s*([A-Z]+)',
        r'([A-Z]+)\s*SHORT'
    ]
    
    # 检查做多信号
    for pattern in long_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            logger.info(f"检测到做多信号: {symbol}")
            return '做多', symbol
    
    # 检查做空信号
    for pattern in short_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            logger.info(f"检测到做空信号: {symbol}")
            return '做空', symbol
    
    logger.debug("未检测到交易信号")
    return None, None

def extract_close_signal(message):
    logger.debug(f"正在从消息中提取平仓信号: {message[:100]}...")
    
    # 平仓信号
    close_patterns = [
        r'平仓\s*([A-Z]+)',
        r'([A-Z]+)\s*平仓',
        r'平多\s*([A-Z]+)',
        r'([A-Z]+)\s*平多',
        r'平空\s*([A-Z]+)',
        r'([A-Z]+)\s*平空',
        r'CLOSE\s*([A-Z]+)',
        r'([A-Z]+)\s*CLOSE'
    ]
    
    for pattern in close_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            logger.info(f"检测到平仓信号: {symbol}")
            return 'both', symbol
    
    logger.debug("未检测到平仓信号")
    return None, None

def get_shanghai_time():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz)

def generate_clord_id():
    return f"TG{int(time.time())}{random.randint(1000, 9999)}"

def set_leverage(account, symbols):
    try:
        account_api = Account.AccountAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        
        for symbol in symbols:
            symbol_id = f"{symbol}-USDT-SWAP"
            response = account_api.set_leverage(
                instId=symbol_id,
                lever=str(account['LEVERAGE']),
                mgnMode='cross'
            )
            if response.get('code') == '0':
                logger.info(f"账号 {account['account_name']} 设置 {symbol} 杠杆成功: {account['LEVERAGE']}x")
            else:
                logger.error(f"账号 {account['account_name']} 设置 {symbol} 杠杆失败: {response}")
    except Exception as e:
        logger.error(f"设置杠杆时出错: {e}")
        logger.error(traceback.format_exc())

def get_latest_market_price(symbol):
    try:
        market_api = MarketData.MarketAPI(debug=False)
        symbol_id = f"{symbol}-USDT-SWAP"
        response = market_api.get_ticker(instId=symbol_id)
        if response.get('code') == '0':
            return float(response['data'][0]['last'])
        else:
            logger.error(f"获取 {symbol} 市场价格失败: {response}")
            return None
    except Exception as e:
        logger.error(f"获取市场价格时出错: {e}")
        return None

def place_order(account, action, symbol):
    try:
        trade_api = Trade.TradeAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        
        symbol_id = f"{symbol}-USDT-SWAP"
        side = 'buy' if action == '做多' else 'sell'
        qty = account['FIXED_QTY'].get(symbol, '0.01')
        clord_id = generate_clord_id()
        
        response = trade_api.place_order(
            instId=symbol_id,
            tdMode='cross',
            side=side,
            ordType='market',
            sz=qty,
            clOrdId=clord_id
        )
        
        if response.get('code') == '0':
            order_id = response['data'][0]['ordId']
            market_price = get_latest_market_price(symbol)
            
            # 记录订单信息
            order_info = {
                'timestamp': datetime.utcnow(),
                'account_name': account['account_name'],
                'action': action,
                'symbol': symbol,
                'quantity': float(qty),
                'price': market_price or 0.0,
                'market_price': market_price or 0.0,
                'order_id': order_id,
                'status': '成功',
                'error_message': None,
                'profit_loss': None,
                'close_time': None
            }
            
            log_order(order_info)
            log_system_message('INFO', 'trading', f"下单成功: {account['account_name']} {action} {symbol} {qty}")
            
            logger.info(f"账号 {account['account_name']} {action} {symbol} 下单成功: {order_id}")
            return True
        else:
            error_msg = f"下单失败: {response}"
            logger.error(f"账号 {account['account_name']} {action} {symbol} {error_msg}")
            
            # 记录失败订单
            order_info = {
                'timestamp': datetime.utcnow(),
                'account_name': account['account_name'],
                'action': action,
                'symbol': symbol,
                'quantity': float(qty),
                'price': 0.0,
                'market_price': get_latest_market_price(symbol) or 0.0,
                'order_id': clord_id,
                'status': '失败',
                'error_message': error_msg,
                'profit_loss': None,
                'close_time': None
            }
            
            log_order(order_info)
            log_system_message('ERROR', 'trading', f"下单失败: {account['account_name']} {action} {symbol} - {error_msg}")
            
            return False
    except Exception as e:
        error_msg = f"下单异常: {str(e)}"
        logger.error(f"账号 {account['account_name']} {action} {symbol} {error_msg}")
        logger.error(traceback.format_exc())
        
        # 记录异常订单
        order_info = {
            'timestamp': datetime.utcnow(),
            'account_name': account['account_name'],
            'action': action,
            'symbol': symbol,
            'quantity': 0.0,
            'price': 0.0,
            'market_price': 0.0,
            'order_id': generate_clord_id(),
            'status': '失败',
            'error_message': error_msg,
            'profit_loss': None,
            'close_time': None
        }
        
        log_order(order_info)
        log_system_message('ERROR', 'trading', f"下单异常: {account['account_name']} {action} {symbol} - {error_msg}")
        
        return False

def close_position(account, symbol, close_type='both'):
    try:
        account_api = Account.AccountAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        
        trade_api = Trade.TradeAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        
        symbol_id = f"{symbol}-USDT-SWAP"
        
        # 获取持仓信息
        positions_response = account_api.get_positions(instId=symbol_id)
        if positions_response.get('code') != '0':
            logger.error(f"获取持仓信息失败: {positions_response}")
            return False
        
        positions = positions_response['data']
        close_results = []
        
        for position in positions:
            pos_side = position['posSide']
            pos_size = float(position['pos'])
            
            if pos_size == 0:
                continue
            
            # 根据平仓类型决定是否平仓
            if close_type == 'both' or (close_type == 'long' and pos_side == 'long') or (close_type == 'short' and pos_side == 'short'):
                side = 'sell' if pos_side == 'long' else 'buy'
                clord_id = generate_clord_id()
                
                response = trade_api.place_order(
                    instId=symbol_id,
                    tdMode='cross',
                    side=side,
                    ordType='market',
                    sz=str(pos_size),
                    clOrdId=clord_id
                )
                
                if response.get('code') == '0':
                    order_id = response['data'][0]['ordId']
                    close_results.append({
                        'pos_side': pos_side,
                        'size': pos_size,
                        'order_id': order_id
                    })
                    logger.info(f"账号 {account['account_name']} 平仓 {pos_side} {symbol} 成功: {order_id}")
                else:
                    logger.error(f"账号 {account['account_name']} 平仓 {pos_side} {symbol} 失败: {response}")
        
        if close_results:
            log_system_message('INFO', 'trading', f"平仓完成: {account['account_name']} {symbol} {len(close_results)}个持仓")
            return True
        else:
            logger.info(f"账号 {account['account_name']} 在 {symbol} 上没有需要平仓的持仓")
            return False
            
    except Exception as e:
        logger.error(f"平仓时出错: {e}")
        logger.error(traceback.format_exc())
        log_system_message('ERROR', 'trading', f"平仓异常: {account['account_name']} {symbol} - {str(e)}")
        return False

class BotManager:
    def __init__(self):
        self.restart_interval = timedelta(minutes=30)
        self.stop_event = threading.Event()
        self.bot_thread = None
        self.last_start = None
        self.client = None
        # 使用Northflank Volumes路径
        self.pid_file = os.path.join(DATA_PATH, 'tg_bot.pid')
        self.log_file = os.path.join(LOGS_PATH, 'tg_bot_daemon.log')

    def start_bot(self):
        while not self.stop_event.is_set():
            try:
                self.last_start = datetime.now()
                logger.info(f"开始新的机器人会话，计划运行到: {self.last_start + self.restart_interval}")
                asyncio.run(self.bot_main_loop())
                if self.stop_event.is_set():
                    break
                logger.info(f"等待2秒后重启...")
                time.sleep(2)
            except Exception as e:
                logger.error(f"机器人会话出错: {e}")
                logger.error(traceback.format_exc())
                time.sleep(10)

    async def send_restart_notification(self):
        if not self.client or not self.client.is_connected() or TG_LOG_GROUP_ID is None:
            return
        try:
            shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
            restart_message = f"🔄 机器人定时重启\n时间: {shanghai_time}\n"
            await self.client.send_message(TG_LOG_GROUP_ID, restart_message)
        except Exception as e:
            logger.error(f"发送重启通知失败: {e}")

    async def bot_main_loop(self):
        try:
            logger.info("=" * 50)
            logger.info("Telegram 交易机器人启动")
            logger.info(f"启动时间: {get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"数据存储路径: {DATA_PATH}")
            logger.info(f"Session文件路径: {SESSION_FILE}")
            logger.info("=" * 50)

            for account in OKX_ACCOUNTS:
                logger.info(f"账号: {account['account_name']}, 杠杆倍数: {account['LEVERAGE']}")
            for account in OKX_ACCOUNTS:
                set_leverage(account, ['ETH', 'BTC'])

            logger.info(f"监听群组 IDs: {TG_GROUP_IDS}")

            # 使用Northflank Volumes中的Session文件
            self.client = TelegramClient(
                SESSION_FILE,
                int(TG_API_ID),
                str(TG_API_HASH),
                connection_retries=5,
                timeout=30
            )

            @self.client.on(events.NewMessage(chats=TG_GROUP_IDS))
            async def handler(event):
                message_text = event.message.text
                shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
                group_title = f"群组ID:{event.chat_id}"
                logger.info(f"收到来自[{group_title}]的新消息")
                logger.debug(f"完整消息内容: {message_text}")
                sender = await event.get_sender()
                sender_name = sender.username if sender.username else (sender.first_name or "") + (sender.last_name or "")
                base_log = f"时间: {shanghai_time}\n来源: {group_title} (@{sender_name})\n消息: {message_text[:300]}{'...' if len(message_text) > 300 else ''}"

                # 记录Telegram消息到数据库
                message_data = {
                    'timestamp': datetime.utcnow(),
                    'group_id': str(event.chat_id),
                    'group_title': group_title,
                    'sender_name': sender_name,
                    'message_text': message_text,
                    'has_signal': False,
                    'signal_type': None,
                    'signal_action': None,
                    'signal_symbol': None
                }

                # 提取交易信息
                action, symbol = extract_trade_info(message_text)
                # 提取平仓信号
                close_type, close_symbol = extract_close_signal(message_text)
                
                # 更新消息数据
                if action and symbol:
                    message_data['has_signal'] = True
                    message_data['signal_type'] = '交易信号'
                    message_data['signal_action'] = action
                    message_data['signal_symbol'] = symbol
                elif close_type and close_symbol:
                    message_data['has_signal'] = True
                    message_data['signal_type'] = '平仓信号'
                    message_data['signal_action'] = close_type
                    message_data['signal_symbol'] = close_symbol
                
                # 记录消息到数据库
                log_telegram_message(message_data)
                
                # 合并消息发送到日志群组
                combined_message = f"📥 收到消息:\n{base_log}"
                
                if action and symbol:
                    combined_message += f"\n\n✅ 检测到交易信号!\n动作: {action}\n符号: {symbol}"
                elif close_type and close_symbol:
                    combined_message += f"\n\n🔄 检测到平仓信号!\n类型: {close_type}\n符号: {close_symbol}"
                else:
                    combined_message += f"\n\n📭 未检测到交易信号"

                # 发送合并消息到日志群组
                if TG_LOG_GROUP_ID is not None:
                    try:
                        if len(combined_message) > 3000:
                            parts = [combined_message[i:i + 3000] for i in range(0, len(combined_message), 3000)]
                            for i, part in enumerate(parts):
                                prefix = f"📥 消息内容 (第 {i + 1}/{len(parts)} 部分):\n"
                                await self.client.send_message(TG_LOG_GROUP_ID, prefix + part)
                        else:
                            await self.client.send_message(TG_LOG_GROUP_ID, combined_message)
                        logger.info("消息已发送到日志记录群组")
                    except Exception as e:
                        logger.error(f"发送到日志群组失败: {e}")
                        logger.error(traceback.format_exc())

                # 处理交易信号
                if action and symbol:
                    try:
                        market_price = get_latest_market_price(symbol)
                        logger.info(f"最新市场价格: {market_price}")
                        bark_message = f"时间: {shanghai_time}\n交易信号: {action} {symbol}\n市场价格: {market_price}"
                        if send_bark_notification(BARK_API_KEY, "新的交易信号", bark_message):
                            logger.info("Bark 通知发送成功")
                        else:
                            logger.warning("Bark 通知发送失败")
                        
                        if action not in ['做多', '做空']:
                            no_order_log = f"ℹ️ 无需下单: 不支持的交易动作 '{action}'\n时间: {shanghai_time}\n详情: {action} {symbol}\n市场价格: {market_price}"
                            if TG_LOG_GROUP_ID is not None:
                                await self.client.send_message(TG_LOG_GROUP_ID, no_order_log)
                            logger.info(f"无需下单: 不支持的交易动作 '{action}'")
                            return
                        
                        for account in OKX_ACCOUNTS:
                            logger.info(f"处理账号 {account['account_name']} 的下单...")
                            order_result = place_order(account, action, symbol)
                            if order_result:
                                order_log = f"📊 下单成功!\n时间: {shanghai_time}\n账号: {account['account_name']}\n详情: {action} {symbol}\n市场价格: {market_price}"
                                if TG_LOG_GROUP_ID is not None:
                                    await self.client.send_message(TG_LOG_GROUP_ID, order_log)
                                logger.info("下单结果已发送到日志记录群组")
                                bark_order_message = f"时间: {shanghai_time}\n账号: {account['account_name']}\n下单结果: {action}极速{('做多' if action == '做多' else '做空')}成功\n市场价格: {market_price}"
                                if send_bark_notification(BARK_API_KEY, "下单结果", bark_order_message):
                                    logger.info("Bark 下单通知发送成功")
                                else:
                                    logger.warning("Bark 下单通知失败")
                            else:
                                error_log = f"❌ 下单失败!\n时间: {shanghai_time}\n账号: {account['account_name']}\n详情: {action} {symbol}\n市场价格: {market_price}"
                                if TG_LOG_GROUP_ID is not None:
                                    await self.client.send_message(TG_LOG_GROUP_ID, error_log)
                                logger.error(f"账号 {account['account_name']} 下单失败")
                    except Exception as e:
                        error_msg = f"❌ 处理交易信号时出错!\n时间: {shanghai_time}\n错误: {str(e)}"
                        if TG_LOG_GROUP_ID is not None:
                            await self.client.send_message(TG_LOG_GROUP_ID, error_msg)
                        logger.error(f"处理交易信号时出错: {e}")
                        logger.error(traceback.format_exc())
                
                # 处理平仓信号
                elif close_type and close_symbol:
                    try:
                        market_price = get_latest_market_price(close_symbol)
                        logger.info(f"最新市场价格: {market_price}")
                        bark_message = f"时间: {shanghai_time}\n平仓信号: {close_type} {close_symbol}\n市场价格: {market_price}"
                        if send_bark_notification(BARK_API_KEY, "新的平仓信号", bark_message):
                            logger.info("Bark 平仓通知发送成功")
                        else:
                            logger.warning("Bark 平仓通知发送失败")
                        
                        for account in OKX_ACCOUNTS:
                            logger.info(f"处理账号 {account['account_name']} 的平仓...")
                            close_results = close_position(account, close_symbol, close_type)
                            if close_results:
                                close_log = f"🔄 平仓完成!\n时间: {shanghai_time}\n账号: {account['account_name']}\n详情: {close_type} {close_symbol}\n市场价格: {market_price}\n平仓结果: {len(close_results)} 个持仓"
                                if TG_LOG_GROUP_ID is not None:
                                    await self.client.send_message(TG_LOG_GROUP_ID, close_log)
                                logger.info("平仓结果已发送到日志记录群组")
                                bark_close_message = f"时间: {shanghai_time}\n账号: {account['account_name']}\n平仓结果: {close_type} {close_symbol} 平仓完成\n市场价格: {market_price}"
                                if send_bark_notification(BARK_API_KEY, "平仓结果", bark_close_message):
                                    logger.info("Bark 平仓通知发送成功")
                                else:
                                    logger.warning("Bark 平仓通知失败")
                            else:
                                no_position_log = f"ℹ️ 无需平仓: 账号 {account['account_name']} 在 {close_symbol} 上没有相关持仓\n时间: {shanghai_time}\n详情: {close_type} {close_symbol}\n市场价格: {market_price}"
                                if TG_LOG_GROUP_ID is not None:
                                    await self.client.send_message(TG_LOG_GROUP_ID, no_position_log)
                                logger.info(f"账号 {account['account_name']} 无需平仓")
                    except Exception as e:
                        error_msg = f"❌ 处理平仓信号时出错!\n时间: {shanghai_time}\n错误: {str(e)}"
                        if TG_LOG_GROUP_ID is not None:
                            await self.client.send_message(TG_LOG_GROUP_ID, error_msg)
                        logger.error(f"处理平仓信号时出错: {e}")
                        logger.error(traceback.format_exc())

            await self.client.start()
            logger.info(f"Telegram 客户端已连接，开始监听群组: {TG_GROUP_IDS}")
            start_time = datetime.now()
            while not self.stop_event.is_set():
                if datetime.now() - start_time >= self.restart_interval:
                    logger.info("达到重启时间，准备重启...")
                    await self.send_restart_notification()
                    break
                await asyncio.sleep(30)
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.debug(f"机器人仍在运行，当前时间: {current_time}")
            logger.info("正在断开Telegram连接...")
            if self.client and self.client.is_connected():
                await self.client.disconnect()
        except Exception as e:
            logger.error(f"机器人主循环出错: {e}")
            logger.error(traceback.format_exc())
        finally:
            logger.info("=" * 50)
            logger.info("Telegram 交易机器人停止运行")
            logger.info(f"停止时间: {get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 50)

    def start(self):
        self.stop_event.clear()
        self.bot_thread = threading.Thread(target=self.start_bot, daemon=True)
        self.bot_thread.start()
        logger.info("机器人管理器已启动")

    def stop(self):
        logger.info("停止机器人管理器...")
        self.stop_event.set()
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=30)
        logger.info("机器人管理器已停止")

    def start_with_daemon(self):
        """以守护进程模式启动"""
        try:
            if self.is_running():
                logger.error("机器人已经在运行中")
                return False
            
            pid = os.fork()
            if pid > 0:
                logger.info(f"守护进程已启动，PID: {pid}")
                self.write_pid_file(pid)
                return True
            elif pid == 0:
                os.setsid()
                os.umask(0)
                
                sys.stdout = open(self.log_file, 'a')
                sys.stderr = sys.stdout
                
                self.start()
                
                while True:
                    time.sleep(1)
            else:
                logger.error("创建守护进程失败")
                return False
        except Exception as e:
            logger.error(f"启动守护进程时出错: {e}")
            return False

    def stop_daemon(self):
        """停止守护进程"""
        try:
            if not self.is_running():
                logger.info("机器人未在运行")
                return True
            
            pid = self.read_pid_file()
            if pid:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"已发送停止信号到进程 {pid}")
                
                for i in range(10):
                    if not self.is_running():
                        logger.info("机器人已停止")
                        self.remove_pid_file()
                        return True
                    time.sleep(1)
                
                os.kill(pid, signal.SIGKILL)
                logger.info("强制停止机器人")
                self.remove_pid_file()
                return True
            else:
                logger.error("无法读取PID文件")
                return False
        except Exception as e:
            logger.error(f"停止守护进程时出错: {e}")
            return False

    def is_running(self):
        """检查机器人是否在运行"""
        try:
            pid = self.read_pid_file()
            if not pid:
                return False
            
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def write_pid_file(self, pid):
        """写入PID文件"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
        except Exception as e:
            logger.error(f"写入PID文件失败: {e}")

    def read_pid_file(self):
        """读取PID文件"""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            logger.error(f"读取PID文件失败: {e}")
        return None

    def remove_pid_file(self):
        """删除PID文件"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except Exception as e:
            logger.error(f"删除PID文件失败: {e}")

    def status(self):
        """检查机器人状态"""
        if self.is_running():
            pid = self.read_pid_file()
            logger.info(f"机器人正在运行，PID: {pid}")
            return True
        else:
            logger.info("机器人未在运行")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Telegram 交易机器人')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--stop', action='store_true', help='停止守护进程')
    parser.add_argument('--status', action='store_true', help='检查守护进程状态')
    parser.add_argument('--login', action='store_true', help='仅进行Telegram登录')
    
    args = parser.parse_args()
    
    bot_manager = BotManager()
    
    if args.stop:
        if bot_manager.stop_daemon():
            print("守护进程已停止")
        else:
            print("停止守护进程失败")
        sys.exit(0)
    
    if args.status:
        if bot_manager.status():
            print("守护进程正在运行")
        else:
            print("守护进程未运行")
        sys.exit(0)
    
    if args.login:
        print(f"正在使用电话号码 {TG_PHONE_NUMBER} 登录Telegram...")
        print(f"Session文件将保存到: {SESSION_FILE}")
        client = TelegramClient(
            SESSION_FILE,
            int(TG_API_ID),
            str(TG_API_HASH),
            connection_retries=5,
            timeout=30
        )
        
        try:
            client.start()
            print("登录成功！")
            print(f"Session文件已保存到: {SESSION_FILE}")
            client.disconnect()
        except Exception as e:
            print(f"登录失败: {e}")
        sys.exit(0)
    
    if args.daemon:
        try:
            bot_manager.start_with_daemon()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("接收到中断信号，正在关闭...")
        finally:
            bot_manager.stop()
    else:
        print("正在启动Telegram机器人...")
        print(f"使用电话号码: {TG_PHONE_NUMBER}")
        print(f"数据存储路径: {DATA_PATH}")
        print(f"Session文件路径: {SESSION_FILE}")
        print("如果是第一次运行，请按照提示输入验证码")
        
        try:
            bot_manager.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("接收到键盘中断信号，正在关闭...")
        finally:
            bot_manager.stop() 