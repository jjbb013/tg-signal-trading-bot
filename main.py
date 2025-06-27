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

# 日志设置
def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = f'logs/tg_bot_{current_date}.log'
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
SESSION_NAME = f'session_{TG_PHONE_NUMBER}'

# OKX多账号配置（支持2个及以上账号，扩展只需增加循环范围和环境变量）
OKX_ACCOUNTS = []
for idx in range(1, 6):  # 如需更多账号，扩展此范围
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
    action_pattern = r"执行交易:(.+?)(?= \d+\.\d+\w+)"
    action_match = re.search(action_pattern, message)
    symbol_pattern = r"策略当前交易对:(\w+USDT\.P)"
    symbol_match = re.search(symbol_pattern, message)
    if action_match and symbol_match:
        action = action_match.group(1).strip()
        symbol = symbol_match.group(1).split('USDT')[0]
        logger.info(f"成功提取交易信息 - 动作: {action}, 符号: {symbol}")
        return action, symbol
    else:
        logger.warning("无法从消息中提取交易信息")
        return None, None

def get_shanghai_time():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz)

def generate_clord_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
    return f"TG{timestamp}{random_str}"[:32]

def set_leverage(account, symbols):
    try:
        logger.info(f"正在为账号 {account['account_name']} 设置杠杆倍数...")
        account_api = Account.AccountAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        for symbol in symbols:
            inst_id = f"{symbol}-USDT-SWAP"
            logger.info(f"设置 {inst_id} 的杠杆倍数为 {account['LEVERAGE']}...")
            leverage_result = account_api.set_leverage(
                instId=inst_id,
                lever=str(account['LEVERAGE']),
                mgnMode="cross"
            )
            logger.debug(f"设置杠杆结果: {leverage_result}")
    except Exception as e:
        logger.error(f"设置杠杆倍数时出错: {e}")
        logger.error(traceback.format_exc())

def get_latest_market_price(symbol):
    try:
        market_data_api = MarketData.MarketAPI(flag="1")
        inst_id = f"{symbol}-USDT-SWAP"
        logger.info(f"获取 {inst_id} 的市场价格...")
        ticker = market_data_api.get_ticker(instId=inst_id)
        if not ticker or not ticker.get('data'):
            logger.error("获取市场价格失败")
            return None
        price = float(ticker['data'][0]['last'])
        logger.info(f"最新市场价格: {price}")
        return price
    except Exception as e:
        logger.error(f"获取市场价格时出错: {e}")
        logger.error(traceback.format_exc())
        return None

def place_order(account, action, symbol):
    try:
        logger.info(f"正在为账号 {account['account_name']} 执行下单: {action} {symbol}...")
        trade_api = Trade.TradeAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        market_data_api = MarketData.MarketAPI(flag=account['FLAG'])
        inst_id = f"{symbol}-USDT-SWAP"
        qty = account['FIXED_QTY'][symbol]
        ticker = market_data_api.get_ticker(instId=inst_id)
        if not ticker or not ticker.get('data'):
            logger.error("获取市场价格失败")
            return None
        price = float(ticker['data'][0]['last'])
        logger.info(f"最新市场价格: {price}")
        if action == '做多':
            take_profit_price = round(price * (1 + 0.01), 4)
            stop_loss_price = round(price * (1 - 0.027), 4)
        elif action == '做空':
            take_profit_price = round(price * (1 - 0.01), 4)
            stop_loss_price = round(price * (1 + 0.027), 4)
        else:
            logger.warning(f"未支持的交易动作: {action}, 忽略...")
            return None
        attach_algo_ord = {
            "tpTriggerPx": str(take_profit_price),
            "tpOrdPx": "-1",
            "slTriggerPx": str(stop_loss_price),
            "slOrdPx": "-1",
            "tpTriggerPxType": "last",
            "slTriggerPxType": "last"
        }
        order_params = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': 'buy' if action == '做多' else 'sell',
            'posSide': 'long' if action == '做多' else 'short',
            'ordType': 'market',
            'sz': qty,
            'clOrdId': generate_clord_id(),
            'attachAlgoOrds': [attach_algo_ord]
        }
        logger.debug(f"下单参数: {order_params}")
        order_result = trade_api.place_order(**order_params)
        logger.debug(f"下单结果: {order_result}")
        if order_result and order_result.get('code') == '0' and order_result.get('msg') == '':
            logger.info(f"下单成功! 订单ID: {order_result.get('data')[0].get('ordId')}")
            return order_result
        else:
            logger.error(f"下单失败! 错误信息: {order_result}")
            return None
    except Exception as e:
        logger.error(f"下单时出错: {e}")
        logger.error(traceback.format_exc())
        return None

class BotManager:
    def __init__(self):
        self.restart_interval = timedelta(hours=1)
        self.stop_event = threading.Event()
        self.bot_thread = None
        self.last_start = None
        self.client = None

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
            logger.info("=" * 50)

            for account in OKX_ACCOUNTS:
                logger.info(f"账号: {account['account_name']}, 杠杆倍数: {account['LEVERAGE']}")
            for account in OKX_ACCOUNTS:
                set_leverage(account, ['ETH', 'BTC'])

            logger.info(f"监听群组 IDs: {TG_GROUP_IDS}")

            self.client = TelegramClient(
                SESSION_NAME,
                TG_API_ID,
                TG_API_HASH,
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

                if TG_LOG_GROUP_ID is not None:
                    try:
                        if len(message_text) > 3000:
                            parts = [message_text[i:i + 3000] for i in range(0, len(message_text), 3000)]
                            await self.client.send_message(TG_LOG_GROUP_ID, f"📥 收到消息 (第一部分):\n{base_log}")
                            for i, part in enumerate(parts):
                                prefix = f"📥 消息内容 (第 {i + 1}/{len(parts)} 部分):\n"
                                await self.client.send_message(TG_LOG_GROUP_ID, prefix + part)
                        else:
                            await self.client.send_message(TG_LOG_GROUP_ID, f"📥 收到消息:\n{base_log}")
                        logger.info("消息已发送到日志记录群组")
                    except Exception as e:
                        logger.error(f"发送到日志群组失败: {e}")
                        logger.error(traceback.format_exc())

                action, symbol = extract_trade_info(message_text)
                if action and symbol:
                    trade_log_message = f"✅ 检测到交易信号!\n{base_log}\n动作: {action}\n符号: {symbol}"
                    try:
                        if TG_LOG_GROUP_ID is not None:
                            await self.client.send_message(TG_LOG_GROUP_ID, trade_log_message)
                        logger.info("交易信号已发送到日志记录群组")
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
                else:
                    no_trade_log = f"📭 未检测到交易信号\n{base_log}"
                    if TG_LOG_GROUP_ID is not None:
                        try:
                            await self.client.send_message(TG_LOG_GROUP_ID, no_trade_log)
                            logger.info("无交易信号通知已发送")
                        except Exception as e:
                            logger.error(f"发送无交易信号通知失败: {e}")
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

if __name__ == "__main__":
    bot_manager = BotManager()
    try:
        bot_manager.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到键盘中断信号，正在关闭...")
    finally:
        bot_manager.stop() 