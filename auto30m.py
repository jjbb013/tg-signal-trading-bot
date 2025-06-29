import asyncio
from telethon.sync import TelegramClient
import json
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
import threading
import queue

# 添加消息队列用于历史消息对比
message_queue = queue.Queue(maxsize=1000)
last_messages = {}  # 存储每个群组的最后消息ID

# 设置日志记录
def setup_logger():
    """设置日志记录器"""
    # 确保日志目录存在
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # 生成日志文件名（按日期）
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = f'logs/tg_bot_{current_date}.log'
    debug_log_filename = f'logs/debug_{current_date}.log'

    # 创建主日志记录器
    logger = logging.getLogger('tg_bot')
    logger.setLevel(logging.DEBUG)

    # 创建调试日志记录器
    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)

    # 创建调试文件处理器
    debug_file_handler = logging.FileHandler(debug_log_filename)
    debug_file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    debug_file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    debug_logger.addHandler(debug_file_handler)

    return logger, debug_logger

# 创建日志记录器实例
logger, debug_logger = setup_logger()

# 调试工具函数
def log_raw_event(event):
    """记录原始事件详细信息"""
    try:
        debug_info = {
            'timestamp': datetime.now().isoformat(),
            'event_type': type(event).__name__,
            'event_id': getattr(event, 'id', 'N/A'),
            'chat_id': getattr(event, 'chat_id', 'N/A'),
            'sender_id': getattr(event, 'sender_id', 'N/A'),
            'message': getattr(event, 'message', 'N/A'),
            'raw_text': getattr(event, 'raw_text', 'N/A'),
            'date': getattr(event, 'date', 'N/A'),
            'edit_date': getattr(event, 'edit_date', 'N/A'),
            'post_author': getattr(event, 'post_author', 'N/A'),
            'grouped_id': getattr(event, 'grouped_id', 'N/A'),
            'reply_to_msg_id': getattr(event, 'reply_to_msg_id', 'N/A'),
            'forward': getattr(event, 'forward', 'N/A'),
            'fwd_from': getattr(event, 'fwd_from', 'N/A'),
            'via_bot_id': getattr(event, 'via_bot_id', 'N/A'),
            'media_unread': getattr(event, 'media_unread', 'N/A'),
            'silent': getattr(event, 'silent', 'N/A'),
            'post': getattr(event, 'post', 'N/A'),
            'from_scheduled': getattr(event, 'from_scheduled', 'N/A'),
            'legacy': getattr(event, 'legacy', 'N/A'),
            'edit_hide': getattr(event, 'edit_hide', 'N/A'),
            'restriction_reason': getattr(event, 'restriction_reason', 'N/A'),
            'ttl_period': getattr(event, 'ttl_period', 'N/A'),
        }
        
        debug_logger.info(f"RAW_EVENT: {json.dumps(debug_info, ensure_ascii=False, default=str)}")
        
        # 记录原始事件对象的所有属性
        event_attrs = {}
        for attr in dir(event):
            if not attr.startswith('_'):
                try:
                    value = getattr(event, attr)
                    if not callable(value):
                        event_attrs[attr] = str(value)
                except:
                    event_attrs[attr] = 'ERROR_GETTING_VALUE'
        
        debug_logger.info(f"EVENT_ATTRIBUTES: {json.dumps(event_attrs, ensure_ascii=False, default=str)}")
        
    except Exception as e:
        debug_logger.error(f"记录原始事件失败: {e}")
        debug_logger.error(traceback.format_exc())

def log_message_details(event, message_type="NEW_MESSAGE"):
    """记录消息详细信息"""
    try:
        shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取发送者信息
        sender = None
        sender_name = "Unknown"
        try:
            sender = event.get_sender()
            if sender:
                sender_name = sender.username if sender.username else (sender.first_name or "") + (sender.last_name or "")
        except:
            pass
        
        # 获取聊天信息
        chat = None
        chat_title = f"ChatID:{event.chat_id}"
        try:
            chat = event.get_chat()
            if chat:
                chat_title = getattr(chat, 'title', chat_title)
        except:
            pass
        
        message_details = {
            'timestamp': shanghai_time,
            'message_type': message_type,
            'message_id': event.id,
            'chat_id': event.chat_id,
            'chat_title': chat_title,
            'sender_id': event.sender_id,
            'sender_name': sender_name,
            'message_text': event.message.text if event.message else "No text",
            'message_length': len(event.message.text) if event.message and event.message.text else 0,
            'date': event.date.isoformat() if event.date else "N/A",
            'edit_date': event.edit_date.isoformat() if event.edit_date else "N/A",
            'reply_to_msg_id': event.reply_to_msg_id,
            'forward': bool(event.forward),
            'media': bool(event.media),
            'silent': event.silent,
            'post': event.post,
            'from_scheduled': event.from_scheduled,
        }
        
        debug_logger.info(f"MESSAGE_DETAILS: {json.dumps(message_details, ensure_ascii=False, default=str)}")
        
        # 将消息加入队列用于历史对比
        try:
            message_queue.put_nowait({
                'chat_id': event.chat_id,
                'message_id': event.id,
                'timestamp': shanghai_time,
                'text': event.message.text if event.message else "",
                'details': message_details
            })
        except queue.Full:
            # 队列满了，移除最旧的消息
            try:
                message_queue.get_nowait()
                message_queue.put_nowait({
                    'chat_id': event.chat_id,
                    'message_id': event.id,
                    'timestamp': shanghai_time,
                    'text': event.message.text if event.message else "",
                    'details': message_details
                })
            except:
                pass
                
    except Exception as e:
        debug_logger.error(f"记录消息详情失败: {e}")
        debug_logger.error(traceback.format_exc())

async def fetch_recent_messages(client, chat_id, limit=10):
    """获取最近的消息用于对比"""
    try:
        debug_logger.info(f"开始获取聊天 {chat_id} 的最近 {limit} 条消息")
        
        messages = []
        async for message in client.iter_messages(chat_id, limit=limit):
            if message and message.text:
                msg_info = {
                    'id': message.id,
                    'date': message.date.isoformat() if message.date else "N/A",
                    'text': message.text[:200],  # 只取前200字符
                    'sender_id': message.sender_id,
                    'chat_id': message.chat_id
                }
                messages.append(msg_info)
        
        debug_logger.info(f"获取到 {len(messages)} 条历史消息")
        for msg in messages:
            debug_logger.info(f"HISTORY_MESSAGE: {json.dumps(msg, ensure_ascii=False, default=str)}")
        
        return messages
        
    except Exception as e:
        debug_logger.error(f"获取历史消息失败: {e}")
        debug_logger.error(traceback.format_exc())
        return []

def check_message_consistency(chat_id, realtime_messages, history_messages):
    """检查实时消息和历史消息的一致性"""
    try:
        debug_logger.info(f"开始检查聊天 {chat_id} 的消息一致性")
        
        # 获取实时消息的ID列表
        realtime_ids = set()
        for msg in realtime_messages:
            if msg.get('chat_id') == chat_id:
                realtime_ids.add(msg.get('message_id'))
        
        # 获取历史消息的ID列表
        history_ids = set()
        for msg in history_messages:
            if msg.get('chat_id') == chat_id:
                history_ids.add(msg.get('id'))
        
        # 找出差异
        missing_in_realtime = history_ids - realtime_ids
        missing_in_history = realtime_ids - history_ids
        
        consistency_report = {
            'chat_id': chat_id,
            'realtime_count': len(realtime_ids),
            'history_count': len(history_ids),
            'missing_in_realtime': list(missing_in_realtime),
            'missing_in_history': list(missing_in_history),
            'consistency_rate': len(realtime_ids & history_ids) / len(realtime_ids | history_ids) if realtime_ids | history_ids else 0
        }
        
        debug_logger.info(f"CONSISTENCY_REPORT: {json.dumps(consistency_report, ensure_ascii=False, default=str)}")
        
        if missing_in_realtime:
            debug_logger.warning(f"聊天 {chat_id} 有 {len(missing_in_realtime)} 条消息在实时监听中丢失")
        
        return consistency_report
        
    except Exception as e:
        debug_logger.error(f"检查消息一致性失败: {e}")
        debug_logger.error(traceback.format_exc())
        return None

# 订单日志记录
def log_order_to_file(order_info):
    """将订单信息记录到ordered_list.log文件"""
    try:
        log_file = 'logs/ordered_list.log'
        # 确保logs目录存在
        os.makedirs('logs', exist_ok=True)
        
        # 读取现有日志
        existing_orders = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            existing_orders.append(line.strip())
            except Exception as e:
                logger.error(f"读取订单日志文件失败: {e}")
        
        # 添加新订单记录
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order_record = f"{timestamp} | {json.dumps(order_info, ensure_ascii=False)}"
        existing_orders.append(order_record)
        
        # 写入文件
        with open(log_file, 'w', encoding='utf-8') as f:
            for record in existing_orders:
                f.write(record + '\n')
        
        logger.info(f"订单信息已记录到 {log_file}")
    except Exception as e:
        logger.error(f"记录订单信息失败: {e}")
        logger.error(traceback.format_exc())

def get_order_logs():
    """读取ordered_list.log文件中的订单记录"""
    try:
        log_file = 'logs/ordered_list.log'
        if not os.path.exists(log_file):
            return []
        
        orders = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        # 解析日志格式: timestamp | json_data
                        parts = line.strip().split(' | ', 1)
                        if len(parts) == 2:
                            order_info = json.loads(parts[1])
                            orders.append(order_info)
                    except Exception as e:
                        logger.warning(f"解析订单日志行失败: {line.strip()}, 错误: {e}")
        
        return orders
    except Exception as e:
        logger.error(f"读取订单日志失败: {e}")
        return []


# 加载配置
def load_config():
    """加载 Telegram 配置文件"""
    try:
        logger.info("正在加载 Telegram 配置文件...")
        with open('telegram_config.json', 'r') as config_file:
            config = json.load(config_file)
            logger.info("Telegram 配置文件加载成功")
            return config
    except FileNotFoundError:
        logger.error("配置文件 telegram_config.json 未找到！")
        exit(1)
    except json.JSONDecodeError:
        logger.error("配置文件格式错误！")
        exit(1)


def load_okx_config():
    """加载 OKX 配置文件"""
    try:
        logger.info("正在加载 OKX 配置文件...")
        with open('okx_config.json', 'r') as config_file:
            config = json.load(config_file)
            logger.info("OKX 配置文件加载成功")
            return config
    except FileNotFoundError:
        logger.error("配置文件 okx_config.json 未找到！")
        exit(1)
    except json.JSONDecodeError:
        logger.error("配置文件格式错误！")
        exit(1)


# 加载监听群组
def load_listen_group():
    """加载要监听的群组 IDs"""
    try:
        logger.info("正在加载监听群组列表...")
        with open('listen_group.txt', 'r') as group_file:
            group_ids = []
            for line in group_file:
                if 'ID:' in line:
                    group_id = int(line.split('ID: ')[1])
                    group_ids.append(group_id)
            if not group_ids:
                logger.error("listen_group.txt 文件中没有找到有效的群组 ID！")
                exit(1)
            logger.info(f"已加载 {len(group_ids)} 个监听群组")
            return group_ids
    except FileNotFoundError:
        logger.error("listen_group.txt 文件未找到！")
        exit(1)


# 发送 Bark 通知
def send_bark_notification(bark_api_key, title, message):
    """发送 Bark 通知"""
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
    """从消息中提取交易信息"""
    logger.debug(f"正在从消息中提取交易信息: {message[:100]}...")
    
    # 首先检查是否包含平仓关键词，如果是平仓信号则不提取开仓信息
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if has_close_signal:
        logger.debug("检测到平仓信号，跳过开仓信号提取")
        return None, None
    
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


# 提取平仓信号
def extract_close_signal(message):
    """提取平仓信号"""
    logger.debug(f"正在从消息中提取平仓信号: {message[:100]}...")
    
    # 检查是否包含平仓关键词
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if not has_close_signal:
        return None, None
    
    # 提取交易对信息
    symbol_pattern = r"策略当前交易对:(\w+USDT\.P)"
    symbol_match = re.search(symbol_pattern, message)
    
    if symbol_match:
        symbol = symbol_match.group(1).split('USDT')[0]
        # 确定平仓类型
        if '空止盈' in message or '空止损' in message:
            close_type = 'short'
        elif '多止盈' in message or '多止损' in message:
            close_type = 'long'
        else:
            close_type = 'both'
        
        logger.info(f"成功提取平仓信号 - 类型: {close_type}, 符号: {symbol}")
        return close_type, symbol
    else:
        logger.warning("无法从平仓信号中提取交易对信息")
        return None, None


# 获取当前上海时间
def get_shanghai_time():
    """获取当前上海时间"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz)


# 生成符合OKX要求的clOrdId
def generate_clord_id():
    """生成符合OKX要求的clOrdId：字母数字组合，1-32位"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
    return f"TG{timestamp}{random_str}"[:32]


# 设置杠杆倍数
def set_leverage(account, symbols):
    """设置杠杆倍数"""
    try:
        logger.info(f"正在为账号 {account['account_name']} 设置杠杆倍数...")

        # 初始化 Account API 客户端
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


# 获取最新市场价格
def get_latest_market_price(symbol):
    """获取指定交易对的最新市场价格"""
    try:
        # 初始化 MarketData API
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


# 下单操作
def place_order(account, action, symbol):
    """在 OKX 平台上下单"""
    try:
        logger.info(f"正在极速为账号 {account['account_name']} 执行下单: {action} {symbol}...")

        # 初始化 OKX API 客户端
        trade_api = Trade.TradeAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        # 初始化 MarketData API
        market_data_api = MarketData.MarketAPI(flag=account['FLAG'])

        # 设置交易参数
        inst_id = f"{symbol}-USDT-SWAP"
        qty = account['FIXED_QTY'][symbol]

        # 获取最新市场价格
        logger.info(f"极速获取 {inst_id} 的市场价格...")
        ticker = market_data_api.get_ticker(instId=inst_id)
        if not ticker or not ticker.get('data'):
            logger.error("获取市场价格失败")
            return None
        price = float(ticker['data'][0]['last'])
        logger.info(f"最新市场价格: {price}")

        # 计算止盈止损价格
        if action == '做多':
            logger.info("计算做多止盈止损价格...")
            take_profit_price = round(price * (1 + 0.01), 4)  # 止盈 1%
            stop_loss_price = round(price * (1 - 0.027), 4)  # 止损 2.7%
        elif action == '做空':
            logger.info("计算做空止盈止损价格...")
            take_profit_price = round(price * (1 - 0.01), 4)  # 止盈 1%
            stop_loss_price = round(price * (1 + 0.027), 4)  # 止损 2.7%
        else:
            logger.warning(f"未支持的交易动作: {action}, 忽略...")
            return None
        logger.debug(f"止盈价: {take_profit_price}, 止损价: {stop_loss_price}")

        # 构建止盈止损参数
        attach_algo_ord = {
            "tpTriggerPx": str(take_profit_price),
            "tpOrdPx": "-1",  # 市价止盈
            "slTriggerPx": str(stop_loss_price),
            "slOrdPx": "-1",  # 市价止损
            "tpTriggerPxType": "last",
            "slTriggerPxType": "last"
        }

        # 构建下单参数
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

        # 下单
        logger.info("正在执行下单操作...")
        order_result = trade_api.place_order(**order_params)
        logger.debug(f"下单结果: {order_result}")

        # 检查下单是否成功
        if order_result and order_result.get('code') == '0' and order_result.get('msg') == '':
            order_id = order_result.get('data')[0].get('ordId')
            logger.info(f"下单成功! 订单ID: {order_id}")
            
            # 记录订单信息到日志文件
            order_info = {
                'account_name': account['account_name'],
                'ordId': order_id,
                'clOrdId': order_params['clOrdId'],
                'action': action,
                'symbol': symbol,
                'inst_id': inst_id,
                'side': order_params['side'],
                'posSide': order_params['posSide'],
                'qty': qty,
                'price': price,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            log_order_to_file(order_info)
            
            return order_result
        else:
            logger.error(f"下单失败! 错误信息: {order_result}")
            return None

    except Exception as e:
        logger.error(f"下单时出错: {e}")
        logger.error(traceback.format_exc())
        return None


# 平仓操作
def close_position(account, symbol, close_type='both'):
    """平仓操作"""
    try:
        logger.info(f"正在为账号 {account['account_name']} 执行平仓: {symbol} {close_type}")
        
        # 初始化 Account API
        account_api = Account.AccountAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        
        # 初始化 Trade API
        trade_api = Trade.TradeAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        
        inst_id = f"{symbol}-USDT-SWAP"
        
        # 获取持仓信息
        positions = account_api.get_positions(instId=inst_id)
        logger.debug(f"持仓信息: {positions}")
        
        if not positions or not positions.get('data'):
            logger.info(f"账号 {account['account_name']} 在 {inst_id} 上没有持仓")
            return None
        
        close_results = []
        
        for position in positions['data']:
            pos_side = position.get('posSide')
            pos_sz = float(position.get('pos', '0'))
            
            # 检查是否需要平仓
            should_close = False
            if close_type == 'both':
                should_close = pos_sz > 0
            elif close_type == 'long' and pos_side == 'long':
                should_close = pos_sz > 0
            elif close_type == 'short' and pos_side == 'short':
                should_close = pos_sz > 0
            
            if should_close:
                # 执行平仓
                close_side = 'sell' if pos_side == 'long' else 'buy'
                close_params = {
                    'instId': inst_id,
                    'tdMode': 'cross',
                    'side': close_side,
                    'posSide': pos_side,
                    'ordType': 'market',
                    'sz': str(pos_sz),
                    'clOrdId': generate_clord_id()
                }
                
                logger.info(f"执行平仓: {close_params}")
                close_result = trade_api.place_order(**close_params)
                
                if close_result and close_result.get('code') == '0':
                    close_results.append({
                        'posSide': pos_side,
                        'sz': pos_sz,
                        'ordId': close_result.get('data')[0].get('ordId'),
                        'status': 'success'
                    })
                    logger.info(f"平仓成功: {pos_side} {pos_sz}")
                else:
                    close_results.append({
                        'posSide': pos_side,
                        'sz': pos_sz,
                        'status': 'failed',
                        'error': close_result
                    })
                    logger.error(f"平仓失败: {pos_side} {pos_sz}, 错误: {close_result}")
        
        return close_results if close_results else None
        
    except Exception as e:
        logger.error(f"平仓时出错: {e}")
        logger.error(traceback.format_exc())
        return None


class BotManager:
    """管理机器人生命周期和定时重启"""

    def __init__(self):
        self.restart_interval = timedelta(minutes=30)  # 30分钟重启一次
        self.stop_event = threading.Event()
        self.bot_thread = None
        self.last_start = None
        self.client = None
        self.log_group_id = None
        self.history_check_interval = 300  # 5分钟检查一次历史消息
        self.last_history_check = {}

    def start_bot(self):
        """启动机器人线程"""
        while not self.stop_event.is_set():
            try:
                self.last_start = datetime.now()
                logger.info(f"开始新的机器人会话，计划运行到: {self.last_start + self.restart_interval}")

                # 在单独线程中运行机器人主循环
                asyncio.run(self.bot_main_loop())

                # 检查是否自然终止
                if self.stop_event.is_set():
                    break

                # 正常重启，等待2秒
                logger.info(f"等待2秒后重启...")
                time.sleep(2)

            except Exception as e:
                logger.error(f"机器人会话出错: {e}")
                logger.error(traceback.format_exc())
                # 在出错后等待一段时间再重试
                time.sleep(10)

    async def send_restart_notification(self):
        """发送重启通知（异步版本）"""
        if not self.client or not self.client.is_connected():
            return

        try:
            shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
            restart_message = f"🔄 机器人定时重启\n时间: {shanghai_time}\n"
            await self.client.send_message(self.log_group_id, restart_message)
        except Exception as e:
            logger.error(f"发送重启通知失败: {e}")

    async def bot_main_loop(self):
        """运行机器人主逻辑（异步）"""
        try:
            logger.info("=" * 50)
            logger.info("Telegram 交易机器人启动")
            logger.info(f"启动时间: {get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 50)

            # 加载配置
            logger.info("开始加载配置文件...")
            config = load_config()
            api_id = config['api_id']
            api_hash = config['api_hash']
            phone_number = config['phone_number']
            bark_api_key = config['bark_api_key']
            self.log_group_id = config['log_group_id']

            logger.info("开始加载 OKX 配置文件...")
            # 加载 OKX 配置
            okx_config = load_okx_config()

            # 输出每个账号的配置信息
            for account in okx_config['accounts']:
                logger.info(f"账号: {account['account_name']}, 杠杆倍数: {account['LEVERAGE']}")

            # 设置杠杆倍数
            for account in okx_config['accounts']:
                set_leverage(account, ['ETH', 'BTC'])

            logger.info("开始加载监听群组...")
            # 加载监听群组 ID
            group_ids = load_listen_group()
            logger.info(f"监听群组 IDs: {group_ids}")

            # 加载代理配置
            proxy_config = config.get('proxy', None)
            proxy = None
            if proxy_config:
                proxy = (proxy_config['protocol'], proxy_config['host'], proxy_config['port'])
                logger.info(f"代理配置已加载: {proxy_config['host']}:{proxy_config['port']}")

            # 创建 Telegram 客户端
            logger.info("开始创建 Telegram 客户端...")
            self.client = TelegramClient(
                f'session_{phone_number}',
                api_id,
                api_hash,
                proxy=proxy,
                connection_retries=5,
                timeout=30
            )

            # 设置原始事件监听器（调试用）
            @self.client.on(events.Raw)
            async def raw_handler(event):
                """监听所有原始事件"""
                try:
                    log_raw_event(event)
                except Exception as e:
                    debug_logger.error(f"处理原始事件失败: {e}")

            # 设置消息处理函数
            @self.client.on(events.NewMessage(chats=group_ids))
            async def handler(event):
                # 记录消息详细信息
                log_message_details(event, "NEW_MESSAGE")
                
                # 记录所有消息
                message_text = event.message.text
                shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
                group_title = f"群组ID:{event.chat_id}"

                # 记录到控制台和日志文件
                logger.info(f"收到来自[{group_title}]的新消息")
                logger.debug(f"完整消息内容: {message_text}")

                # 提取发送者信息
                sender = await event.get_sender()
                sender_name = sender.username if sender.username else (sender.first_name or "") + (
                        sender.last_name or "")

                # 创建基础日志消息
                base_log = f"时间: {shanghai_time}\n来源: {group_title} (@{sender_name})\n消息: {message_text[:300]}{'...' if len(message_text) > 300 else ''}"

                # 提取交易信息
                action, symbol = extract_trade_info(message_text)
                # 提取平仓信号
                close_type, close_symbol = extract_close_signal(message_text)
                
                # 合并消息发送到日志群组
                combined_message = f"📥 收到消息:\n{base_log}"
                
                if action and symbol:
                    combined_message += f"\n\n✅ 检测到交易信号!\n动作: {action}\n符号: {symbol}"
                elif close_type and close_symbol:
                    combined_message += f"\n\n🔄 检测到平仓信号!\n类型: {close_type}\n符号: {close_symbol}"
                else:
                    combined_message += f"\n\n📭 未检测到交易信号"

                # 发送合并消息到日志群组
                try:
                    logger.info("发送消息到日志记录群组...")
                    if self.log_group_id is not None:
                        if len(combined_message) > 3000:
                            # 如果消息过长，分成多个部分发送
                            parts = [combined_message[i:i + 3000] for i in range(0, len(combined_message), 3000)]
                            for i, part in enumerate(parts):
                                prefix = f"📥 消息内容 (第 {i + 1}/{len(parts)} 部分):\n"
                                await self.client.send_message(self.log_group_id, prefix + part)
                        else:
                            await self.client.send_message(self.log_group_id, combined_message)
                        logger.info("消息已发送到日志记录群组")
                except Exception as e:
                    logger.error(f"发送到日志群组失败: {e}")
                    logger.error(traceback.format_exc())

                # 处理交易信号
                if action and symbol:
                    try:
                        # 获取最新市场价格
                        logger.info(f"获取 {symbol} 的最新市场价格...")
                        market_price = get_latest_market_price(symbol)
                        logger.info(f"最新市场价格: {market_price}")

                        # 发送 Bark 通知，包含市场价格
                        logger.info("发送 Bark 通知...")
                        bark_message = f"时间: {shanghai_time}\n交易信号: {action} {symbol}\n市场价格: {market_price}"
                        if send_bark_notification(bark_api_key, "新的交易信号", bark_message):
                            logger.info("Bark 通知发送成功")
                        else:
                            logger.warning("Bark 通知发送失败")

                        # 判断交易动作是否支持
                        if action not in ['做多', '做空']:
                            no_order_log = f"ℹ️ 无需下单: 不支持的交易动作 '{action}'\n时间: {shanghai_time}\n详情: {action} {symbol}\n市场价格: {market_price}"
                            if self.log_group_id is not None:
                                await self.client.send_message(self.log_group_id, no_order_log)
                            logger.info(f"无需下单: 不支持的交易动作 '{action}'")
                            return

                        # 对每个账号执行下单操作
                        for account in okx_config['accounts']:
                            logger.info(f"处理账号 {account['account_name']} 的下单...")
                            order_result = place_order(account, action, symbol)
                            if order_result:
                                # 下单成功后发送通知
                                logger.info("发送下单结果到日志记录群组...")
                                order_log = f"📊 下单成功!\n时间: {shanghai_time}\n账号: {account['account_name']}\n详情: {action} {symbol}\n市场价格: {market_price}"
                                if self.log_group_id is not None:
                                    await self.client.send_message(self.log_group_id, order_log)
                                logger.info("下单结果已发送到日志记录群组")

                                bark_order_message = f"时间: {shanghai_time}\n账号: {account['account_name']}\n下单结果: {action}极速{('做多' if action == '做多' else '做空')}成功\n市场价格: {market_price}"
                                if send_bark_notification(bark_api_key, "下单结果", bark_order_message):
                                    logger.info("Bark 下单通知发送成功")
                                else:
                                    logger.warning("Bark 下单通知失败")
                            else:
                                error_log = f"❌ 下单失败!\n时间: {shanghai_time}\n账号: {account['account_name']}\n详情: {action} {symbol}\n市场价格: {market_price}"
                                if self.log_group_id is not None:
                                    await self.client.send_message(self.log_group_id, error_log)
                                logger.error(f"账号 {account['account_name']} 下单失败")
                    except Exception as e:
                        error_msg = f"❌ 处理交易信号时出错!\n时间: {shanghai_time}\n错误: {str(e)}"
                        if self.log_group_id is not None:
                            await self.client.send_message(self.log_group_id, error_msg)
                        logger.error(f"处理交易信号时出错: {e}")
                        logger.error(traceback.format_exc())
                
                # 处理平仓信号
                elif close_type and close_symbol:
                    try:
                        # 获取最新市场价格
                        logger.info(f"获取 {close_symbol} 的最新市场价格...")
                        market_price = get_latest_market_price(close_symbol)
                        logger.info(f"最新市场价格: {market_price}")

                        # 发送 Bark 通知，包含市场价格
                        logger.info("发送 Bark 通知...")
                        bark_message = f"时间: {shanghai_time}\n平仓信号: {close_type} {close_symbol}\n市场价格: {market_price}"
                        if send_bark_notification(bark_api_key, "新的平仓信号", bark_message):
                            logger.info("Bark 平仓通知发送成功")
                        else:
                            logger.warning("Bark 平仓通知发送失败")

                        # 对每个账号执行平仓操作
                        for account in okx_config['accounts']:
                            logger.info(f"处理账号 {account['account_name']} 的平仓...")
                            close_results = close_position(account, close_symbol, close_type)
                            if close_results:
                                # 平仓成功后发送通知
                                logger.info("发送平仓结果到日志记录群组...")
                                close_log = f"🔄 平仓完成!\n时间: {shanghai_time}\n账号: {account['account_name']}\n详情: {close_type} {close_symbol}\n市场价格: {market_price}\n平仓结果: {len(close_results)} 个持仓"
                                if self.log_group_id is not None:
                                    await self.client.send_message(self.log_group_id, close_log)
                                logger.info("平仓结果已发送到日志记录群组")

                                bark_close_message = f"时间: {shanghai_time}\n账号: {account['account_name']}\n平仓结果: {close_type} {close_symbol} 平仓完成\n市场价格: {market_price}"
                                if send_bark_notification(bark_api_key, "平仓结果", bark_close_message):
                                    logger.info("Bark 平仓通知发送成功")
                                else:
                                    logger.warning("Bark 平仓通知失败")
                            else:
                                no_position_log = f"ℹ️ 无需平仓: 账号 {account['account_name']} 在 {close_symbol} 上没有相关持仓\n时间: {shanghai_time}\n详情: {close_type} {close_symbol}\n市场价格: {market_price}"
                                if self.log_group_id is not None:
                                    await self.client.send_message(self.log_group_id, no_position_log)
                                logger.info(f"账号 {account['account_name']} 无需平仓")
                    except Exception as e:
                        error_msg = f"❌ 处理平仓信号时出错!\n时间: {shanghai_time}\n错误: {str(e)}"
                        if self.log_group_id is not None:
                            await self.client.send_message(self.log_group_id, error_msg)
                        logger.error(f"处理平仓信号时出错: {e}")
                        logger.error(traceback.format_exc())

            # 连接到Telegram并启动监听
            await self.client.start()
            logger.info(f"Telegram 客户端已连接，开始监听群组: {group_ids}")

            # 记录开始时间
            start_time = datetime.now()

            # 主循环：每30秒检查一次是否需要重启
            while not self.stop_event.is_set():
                # 检查是否达到重启时间
                if datetime.now() - start_time >= self.restart_interval:
                    logger.info("达到重启时间，准备重启...")
                    await self.send_restart_notification()
                    break

                # 定期检查历史消息一致性
                current_time = time.time()
                for chat_id in group_ids:
                    if current_time - self.last_history_check.get(chat_id, 0) >= self.history_check_interval:
                        try:
                            debug_logger.info(f"开始定期检查聊天 {chat_id} 的消息一致性")
                            
                            # 获取历史消息
                            history_messages = await fetch_recent_messages(self.client, chat_id, limit=20)
                            
                            # 获取实时消息队列中的消息
                            realtime_messages = []
                            while not message_queue.empty():
                                try:
                                    msg = message_queue.get_nowait()
                                    realtime_messages.append(msg)
                                except queue.Empty:
                                    break
                            
                            # 检查一致性
                            consistency_report = check_message_consistency(chat_id, realtime_messages, history_messages)
                            
                            # 更新最后检查时间
                            self.last_history_check[chat_id] = current_time
                            
                        except Exception as e:
                            debug_logger.error(f"检查聊天 {chat_id} 消息一致性失败: {e}")

                # 非阻塞等待30秒（使用异步等待）
                await asyncio.sleep(30)

                # 记录当前时间
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
        """启动机器人管理器"""
        self.stop_event.clear()
        self.bot_thread = threading.Thread(target=self.start_bot, daemon=True)
        self.bot_thread.start()
        logger.info("机器人管理器已启动")

    def stop(self):
        """停止机器人管理器"""
        logger.info("停止机器人管理器...")
        self.stop_event.set()
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=30)
        logger.info("机器人管理器已停止")


if __name__ == "__main__":
    bot_manager = BotManager()

    try:
        bot_manager.start()
        # 主线程保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到键盘中断信号，正在关闭...")
    finally:
        bot_manager.stop()