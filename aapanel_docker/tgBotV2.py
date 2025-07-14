import os
import sys
import time
import asyncio
import logging
import re
from datetime import datetime, timedelta
from telethon.sync import TelegramClient
from telethon import events
from utils import get_shanghai_time, send_bark_notification, build_order_params, set_account_leverage
import okx.Trade as Trade
import okx.MarketData as MarketData
import okx.Account as Account
import json

from dotenv import load_dotenv
load_dotenv('.env')
print("TG_API_ID from env:", os.getenv("TG_API_ID"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('tgBotV2')

SESSION_DIR = os.getenv('SESSION_DIR', './data/sessions')
os.makedirs(SESSION_DIR, exist_ok=True)

LAST_SESSION_PATH_FILE = os.path.join(SESSION_DIR, '../last_session_path.txt')

# 优先读取上次使用的 session 文件
if os.path.exists(LAST_SESSION_PATH_FILE):
    with open(LAST_SESSION_PATH_FILE, 'r', encoding='utf-8') as f:
        session_file = f.read().strip()
    print(f'自动复用上次 session 文件: {session_file}')
else:
    sessions = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    if sessions:
        print('检测到以下 Telegram session 文件：')
        for idx, s in enumerate(sessions):
            print(f'{idx+1}: {s}')
        choice = input('请选择要使用的 session 文件编号，或输入 n 新建登录: ')
        if choice.isdigit() and 1 <= int(choice) <= len(sessions):
            session_file = os.path.join(SESSION_DIR, sessions[int(choice)-1])
        else:
            session_file = os.path.join(SESSION_DIR, f'session_{int(time.time())}.session')
    else:
        print('未检测到 session 文件，将新建登录')
        session_file = os.path.join(SESSION_DIR, f'session_{int(time.time())}.session')
    # 记录本次选择
    with open(LAST_SESSION_PATH_FILE, 'w', encoding='utf-8') as f:
        f.write(session_file)

TG_API_ID = os.getenv('TG_API_ID')
TG_API_HASH = os.getenv('TG_API_HASH')
TG_LOG_GROUP_ID = os.getenv('TG_LOG_GROUP_ID')
TG_CHANNEL_IDS = os.getenv('TG_CHANNEL_IDS', '')
if not TG_API_ID or not TG_API_HASH or not TG_CHANNEL_IDS:
    logger.error('请配置 TG_API_ID, TG_API_HASH, TG_CHANNEL_IDS 环境变量')
    sys.exit(1)
TG_API_ID = int(TG_API_ID)
TG_LOG_GROUP_ID = int(TG_LOG_GROUP_ID) if TG_LOG_GROUP_ID else None
CHANNEL_IDS = [int(cid.strip()) for cid in TG_CHANNEL_IDS.split(',') if cid.strip()]

client = TelegramClient(session_file, TG_API_ID, TG_API_HASH)

# 读取测试账户配置
def get_test_accounts():
    accounts = []
    for idx in range(1, 6):  # 支持最多5个账户
        prefix = f'OKX{idx}_'
        api_key = os.getenv(prefix + 'API_KEY')
        secret_key = os.getenv(prefix + 'SECRET_KEY')
        passphrase = os.getenv(prefix + 'PASSPHRASE')
        flag = os.getenv(prefix + 'FLAG', '1')
        
        if api_key and secret_key and passphrase:
            accounts.append({
                'account_idx': idx,
                'account_name': f'OKX{idx}',
                'API_KEY': api_key,
                'SECRET_KEY': secret_key,
                'PASSPHRASE': passphrase,
                'FLAG': flag
            })
            logger.info(f"加载账户配置: OKX{idx}")
    
    logger.info(f"共检测到 {len(accounts)} 个有效OKX账户")
    if not accounts:
        logger.warning("未检测到任何OKX账户配置")
    return accounts

TEST_ACCOUNTS = get_test_accounts()

PROCESSED_IDS_FILE = 'processed_message_ids.json'

# 加载/保存消息ID缓存

def load_processed_ids():
    try:
        with open(PROCESSED_IDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 转为 set 方便后续处理
            return {int(k): set(v) for k, v in data.items()}
    except Exception:
        return {}

def save_processed_ids(processed_ids):
    try:
        # set 转 list 方便序列化
        data = {str(k): list(v) for k, v in processed_ids.items()}
        with open(PROCESSED_IDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存消息ID缓存失败: {e}")

# 初始化缓存
PROCESSED_MESSAGE_IDS = load_processed_ids()

# 提取信号中的价格，如“ETH价格:2633.96”
def extract_signal_price(message):
    match = re.search(r"[A-Z]+价格[:：]([0-9]+\.?[0-9]*)", message)
    if match:
        return float(match.group(1))
    return None

async def init_processed_ids():
    updated = False
    for channel_id in CHANNEL_IDS:
        if channel_id not in PROCESSED_MESSAGE_IDS:
            PROCESSED_MESSAGE_IDS[channel_id] = set()
        async for message in client.iter_messages(channel_id, limit=20):
            if message and message.id not in PROCESSED_MESSAGE_IDS[channel_id]:
                PROCESSED_MESSAGE_IDS[channel_id].add(message.id)
                updated = True
    if updated:
        save_processed_ids(PROCESSED_MESSAGE_IDS)

# ===== 可调参数区 =====
# 支持通过环境变量设置（单位：秒），如未设置则用默认值
AUTO_RESTART_INTERVAL = int(os.getenv('AUTO_RESTART_INTERVAL', 1800))  # 自动重启间隔，默认30分钟
PATCH_MISSING_SIGNALS_INTERVAL = int(os.getenv('PATCH_MISSING_SIGNALS_INTERVAL', 30))  # 定时补单检查间隔，默认30秒
# =====================

async def check_and_patch_missing_signals():
    while True:
        logger.info('【定时补单检查】正在检查各频道最近20条消息...')
        # 每次定时检查前都重新加载缓存，实现热编辑支持
        global PROCESSED_MESSAGE_IDS
        PROCESSED_MESSAGE_IDS = load_processed_ids()
        try:
            for channel_id in CHANNEL_IDS:
                if channel_id not in PROCESSED_MESSAGE_IDS:
                    PROCESSED_MESSAGE_IDS[channel_id] = set()
                async for message in client.iter_messages(channel_id, limit=20):
                    if not message or not message.text:
                        continue
                    msg_id = message.id
                    if msg_id in PROCESSED_MESSAGE_IDS[channel_id]:
                        continue
                    # 只处理新消息
                    PROCESSED_MESSAGE_IDS[channel_id].add(msg_id)
                    save_processed_ids(PROCESSED_MESSAGE_IDS)
                    msg_text = message.text
                    action, symbol = extract_trade_info(msg_text)
                    close_type, close_symbol = extract_close_signal(msg_text)
                    signal_price = extract_signal_price(msg_text)
                    # 补开仓信号
                    if action and symbol:
                        # 做多/做空需比价
                        if action in ['做多', '做空'] and signal_price:
                            market_price = get_latest_market_price(symbol)
                            if not market_price:
                                logger.warning(f"补单时获取市场价失败: {symbol}")
                                continue
                            price_diff = (market_price - signal_price) / signal_price
                            bark_title = f"补单价格检查-{action}-{symbol}"
                            if action == '做多':
                                if market_price <= signal_price:
                                    await process_open_signal(action, symbol, signal_price)
                                elif 0 < price_diff <= 0.005:
                                    await process_open_signal(action, symbol, signal_price)
                                else:
                                    content = f"做多信号，市场价高于信号价超0.5%，不下单\n信号价:{signal_price}, 市场价:{market_price}"
                                    logger.warning(content)
                                    send_bark_notification(bark_title, content)
                                    if TG_LOG_GROUP_ID:
                                        await client.send_message(TG_LOG_GROUP_ID, content)
                            elif action == '做空':
                                if market_price >= signal_price:
                                    await process_open_signal(action, symbol, signal_price)
                                elif 0 < -price_diff <= 0.005:
                                    await process_open_signal(action, symbol, signal_price)
                                else:
                                    content = f"做空信号，市场价低于信号价超0.5%，不下单\n信号价:{signal_price}, 市场价:{market_price}"
                                    logger.warning(content)
                                    send_bark_notification(bark_title, content)
                                    if TG_LOG_GROUP_ID:
                                        await client.send_message(TG_LOG_GROUP_ID, content)
                        else:
                            # 其他信号或无价格，直接补单
                            await process_open_signal(action, symbol, signal_price or 0)
                    # 补平仓信号
                    elif close_type and close_symbol:
                        await process_close_signal(close_type, close_symbol)
        except Exception as e:
            logger.error(f"历史消息补单检查异常: {e}")
        await asyncio.sleep(PATCH_MISSING_SIGNALS_INTERVAL)

def extract_trade_info(message):
    """从消息中提取开仓交易信息"""
    logger.debug(f"正在从消息中提取交易信息: {message[:100]}...")
    
    # 首先检查是否包含平仓关键词，如果是平仓信号则不提取开仓信息
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损', '平多', '平空']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if has_close_signal:
        logger.debug("检测到平仓信号，跳过开仓信号提取")
        return None, None
    
    # 尝试从标准格式中提取
    action_pattern = r"执行交易[:：]?(.+?)(?= \d+\.\d+\w+)"
    action_match = re.search(action_pattern, message)
    symbol_pattern = r"策略当前交易对[:：]?(\w+USDT\.P)"
    symbol_match = re.search(symbol_pattern, message)
    
    if action_match and symbol_match:
        action = action_match.group(1).strip()
        symbol = symbol_match.group(1).split('USDT')[0]
        logger.info(f"成功提取交易信息 - 动作: {action}, 符号: {symbol}")
        return action, symbol
    
    # 如果标准格式不匹配，使用通用正则表达式
    # 做多信号 - 支持多种格式
    long_patterns = [
        r'做多\s*([A-Z]+)',  # 做多 ETH
        r'([A-Z]+)\s*做多',  # ETH 做多
        r'买入\s*([A-Z]+)',  # 买入 ETH
        r'([A-Z]+)\s*买入',  # ETH 买入
        r'LONG\s*([A-Z]+)',  # LONG ETH
        r'([A-Z]+)\s*LONG',  # ETH LONG
        r'做多\s*\d+\.?\d*([A-Z]+)',  # 做多 0.072ETH
        r'([A-Z]+)\s*做多\s*\d+\.?\d*',  # ETH 做多 0.072
        r'买入\s*\d+\.?\d*([A-Z]+)',  # 买入 0.072ETH
        r'([A-Z]+)\s*买入\s*\d+\.?\d*',  # ETH 买入 0.072
    ]
    
    # 做空信号 - 支持多种格式
    short_patterns = [
        r'做空\s*([A-Z]+)',  # 做空 ETH
        r'([A-Z]+)\s*做空',  # ETH 做空
        r'卖出\s*([A-Z]+)',  # 卖出 ETH
        r'([A-Z]+)\s*卖出',  # ETH 卖出
        r'SHORT\s*([A-Z]+)',  # SHORT ETH
        r'([A-Z]+)\s*SHORT',  # ETH SHORT
        r'做空\s*\d+\.?\d*([A-Z]+)',  # 做空 0.072ETH
        r'([A-Z]+)\s*做空\s*\d+\.?\d*',  # ETH 做空 0.072
        r'卖出\s*\d+\.?\d*([A-Z]+)',  # 卖出 0.072ETH
        r'([A-Z]+)\s*卖出\s*\d+\.?\d*',  # ETH 卖出 0.072
    ]
    
    # 检查做多信号
    for pattern in long_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            logger.info(f"检测到做多信号: {symbol}")
            return '做多', symbol
    
    # 检查做空信号
    for pattern in short_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            logger.info(f"检测到做空信号: {symbol}")
            return '做空', symbol
    
    logger.debug("未检测到开仓交易信号")
    return None, None

def extract_close_signal(message):
    """从消息中提取平仓信号"""
    logger.debug(f"正在从消息中提取平仓信号: {message[:100]}...")

    # 先判断多空止盈止损和平多/平空
    if any(kw in message for kw in ['空止盈', '空止损', '平空']):
        symbol_match = re.search(r'([A-Z]+)', message)
        if symbol_match:
            symbol = symbol_match.group(1).upper().split('USDT')[0]
            logger.info(f"检测到平空/空止盈/空止损信号: {symbol}")
            return 'short', symbol
        else:
            logger.warning("未能从平空/空止盈/空止损信号中提取币种")
            return 'short', None
    if any(kw in message for kw in ['多止盈', '多止损', '平多']):
        symbol_match = re.search(r'([A-Z]+)', message)
        if symbol_match:
            symbol = symbol_match.group(1).upper().split('USDT')[0]
            logger.info(f"检测到平多/多止盈/多止损信号: {symbol}")
            return 'long', symbol
        else:
            logger.warning("未能从平多/多止盈/多止损信号中提取币种")
            return 'long', None
    logger.debug("未检测到平仓信号")
    return None, None

def get_order_size(account_idx, symbol):
    coin = symbol.split('-')[0] if '-' in symbol else symbol
    env_name = f"OKX{account_idx}_FIXED_QTY_{coin}"
    val = os.getenv(env_name)
    if val:
        try:
            return float(val)
        except Exception:
            return None
    return None

def get_latest_market_price(symbol):
    """获取最新市场价格"""
    try:
        market_api = MarketData.MarketAPI(debug=False)
        symbol_id = f"{symbol.upper()}-USDT-SWAP"
        response = market_api.get_ticker(instId=symbol_id)
        if response.get('code') == '0':
            return float(response['data'][0]['last'])
        else:
            logger.error(f"获取 {symbol} 市场价格失败: {response}")
            return None
    except Exception as e:
        logger.error(f"获取市场价格时出错: {e}")
        return None

def build_bark_content(signal, account_name, entry_price, size, margin, take_profit, stop_loss, clOrdId, okx_resp=None, error_msg=None):
    now = get_shanghai_time()
    lines = [
        f"账户: {account_name}",
        f"交易标的: {signal['symbol']}",
        f"信号类型: {signal['action']}",
        f"入场价格: {entry_price:.4f}",
        f"委托数量: {size:.2f}",
        f"保证金: {margin} USDT",
        f"止盈价格: {take_profit:.4f}",
        f"止损价格: {stop_loss:.4f}",
        f"客户订单ID: {clOrdId}",
        f"时间: {now}"
    ]
    if error_msg:
        lines.append("⚠️ 下单失败 ⚠️")
        lines.append(f"错误: {error_msg}")
    if okx_resp:
        lines.append(f"服务器响应代码: {okx_resp.get('code', '')}")
        lines.append(f"服务器响应消息: {okx_resp.get('msg', '')}")
    return "\n".join(lines)

def build_close_bark_content(close_type, symbol, account_name, close_results, okx_resp=None, error_msg=None):
    now = get_shanghai_time()
    lines = [
        f"账户: {account_name}",
        f"交易标的: {symbol}",
        f"信号类型: {close_type}",
        f"平仓结果: {len(close_results)} 个持仓",
        f"时间: {now}"
    ]
    if close_results:
        for result in close_results:
            lines.append(f"- {result['pos_side']}: {result['size']} (订单ID: {result['order_id']})")
    if error_msg:
        lines.append("⚠️ 平仓失败 ⚠️")
        lines.append(f"错误: {error_msg}")
    if okx_resp:
        lines.append(f"服务器响应代码: {okx_resp.get('code', '')}")
        lines.append(f"服务器响应消息: {okx_resp.get('msg', '')}")
    return "\n".join(lines)

async def place_okx_order(account, action, symbol, size):
    """真实的OKX下单函数"""
    try:
        trade_api = Trade.TradeAPI(
            account['API_KEY'],
            account['SECRET_KEY'],
            account['PASSPHRASE'],
            False,
            account['FLAG']
        )
        symbol_id = f"{symbol.upper()}-USDT-SWAP"
        market_price = get_latest_market_price(symbol)
        if market_price is None:
            logger.error(f"无法获取 {symbol} 最新价格，无法下单")
            return {
                "success": False,
                "error_msg": "无法获取市场价格"
            }
        # 计算止盈止损
        if action == '做多':
            side = 'buy'
            pos_side = 'long'
            take_profit = round(market_price * 1.01, 2)  # 止盈1%
            stop_loss = round(market_price * (1 - 0.027), 2)  # 止损2.7%
        elif action == '做空':
            side = 'sell'
            pos_side = 'short'
            take_profit = round(market_price * (1 - 0.01), 2)  # 止盈1%
            stop_loss = round(market_price * (1 + 0.027), 2)  # 止损2.7%
        else:
            logger.error(f"未知的交易动作: {action}")
            return {
                "success": False,
                "error_msg": f"未知的交易动作: {action}"
            }
        leverage = int(os.getenv(f"OKX{account['account_idx']}_LEVERAGE", 10))
        margin = round(market_price * size / leverage, 4)
        logger.info(f"保证金计算参数: 市价={market_price}, 数量={size}, 杠杆={leverage}, 保证金={margin}")
        order_params = build_order_params(
            symbol_id, side, market_price, size, pos_side, take_profit, stop_loss
        )
        # 打印下单参数原始json
        print("下单参数:", json.dumps(order_params, ensure_ascii=False, indent=2))
        response = trade_api.place_order(**order_params)
        # 打印服务器返回原始json
        print("服务器返回:", json.dumps(response, ensure_ascii=False, indent=2))
        if response.get('code') == '0' and response.get('data') and len(response['data']) > 0:
            order_id = response['data'][0].get('ordId', '')
            cl_ord_id = order_params['clOrdId']
            return {
                "success": True,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "margin": margin,
                "clOrdId": cl_ord_id,
                "okx_resp": response,
                "market_price": market_price
            }
        else:
            error_msg = None
            if response.get('data') and isinstance(response['data'], list) and len(response['data']) > 0:
                error_msg = response['data'][0].get('sMsg', '下单失败')
            else:
                error_msg = response.get('msg', '下单失败')
            return {
                "success": False,
                "error_msg": error_msg,
                "okx_resp": response,
                "market_price": market_price
            }
    except Exception as e:
        logger.error(f"下单时出错: {e}")
        return {
            "success": False,
            "error_msg": str(e)
        }

async def fake_close_position(account_idx, symbol, close_type):
    """模拟平仓函数"""
    close_results = [
        {
            'pos_side': 'long' if close_type == 'long' else 'short',
            'size': 0.05,
            'order_id': f"CLOSE{int(time.time())}{account_idx}"
        }
    ]
    okx_resp = {"code": "0", "msg": "模拟平仓成功"}
    return {
        "success": True,
        "close_results": close_results,
        "okx_resp": okx_resp
    }

async def close_okx_position(account, symbol, close_type):
    """真实的OKX平仓函数，只平当前信号方向的仓位"""
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
        symbol_id = f"{symbol.upper()}-USDT-SWAP"
        # 获取持仓信息
        positions_response = account_api.get_positions(instId=symbol_id)
        if positions_response.get('code') != '0':
            logger.error(f"获取持仓信息失败: {positions_response}")
            return {
                "success": False,
                "close_results": [],
                "okx_resp": positions_response,
                "error_msg": "获取持仓信息失败"
            }
        positions = positions_response['data']
        close_results = []
        for position in positions:
            pos_side = position['posSide']
            pos_size = float(position['pos'])
            if pos_size == 0:
                continue
            # 只平当前信号方向的仓位
            if (close_type == 'long' and pos_side == 'long') or (close_type == 'short' and pos_side == 'short'):
                # 平多：side=sell, posSide=long；平空：side=buy, posSide=short
                side = 'sell' if pos_side == 'long' else 'buy'
                clord_id = f"CLOSE{int(time.time())}{account['account_idx']}"
                response = trade_api.place_order(
                    instId=symbol_id,
                    tdMode='cross',
                    side=side,
                    posSide=pos_side,
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
            return {
                "success": True,
                "close_results": close_results,
                "okx_resp": {"code": "0", "msg": "平仓完成"}
            }
        else:
            logger.info(f"账号 {account['account_name']} 在 {symbol} 上没有需要平仓的持仓")
            return {
                "success": True,
                "close_results": [],
                "okx_resp": {"code": "0", "msg": "无持仓可平"}
            }
    except Exception as e:
        logger.error(f"平仓时出错: {e}")
        return {
            "success": False,
            "close_results": [],
            "okx_resp": {},
            "error_msg": str(e)
        }

async def process_open_signal(action, symbol, price):
    """处理开仓信号"""
    for account in TEST_ACCOUNTS:
        size = get_order_size(account['account_idx'], symbol)
        if not size:
            logger.warning(f"未配置账户{account['account_name']}的下单数量，跳过")
            continue
        logger.info(f"准备为账户 {account['account_name']} 下单，参数如下：")
        logger.info(f"action: {action}, symbol: {symbol}, size: {size}")
        order_result = await place_okx_order(account, action, symbol, size)
        logger.info(f"下单返回结果: {order_result}")
        bark_title = f"Tg信号策略{action}-{symbol}"
        # entry_price 用实际下单市场价
        entry_price = order_result.get('market_price', 0)
        bark_content = build_bark_content(
            signal={'symbol': symbol, 'action': action},
            account_name=account['account_name'],
            entry_price=entry_price,
            size=size,
            margin=order_result.get('margin', 0),
            take_profit=order_result.get('take_profit', 0),
            stop_loss=order_result.get('stop_loss', 0),
            clOrdId=order_result.get('clOrdId', ''),
            okx_resp=order_result.get('okx_resp'),
            error_msg=order_result.get('error_msg')
        )
        logger.info(f"准备发送Bark通知，参数如下：title={bark_title}, content={bark_content}")
        send_bark_notification(bark_title, bark_content)
        logger.info(f"Bark通知已发送: {bark_title}")

async def process_close_signal(close_type, symbol):
    """处理平仓信号"""
    for account in TEST_ACCOUNTS:
        logger.info(f"准备为账户 {account['account_name']} 平仓，参数如下：close_type: {close_type}, symbol: {symbol}")
        close_result = await close_okx_position(account, symbol, close_type)
        logger.info(f"平仓返回结果: {close_result}")
        bark_title = f"Tg信号策略平仓-{symbol}"
        bark_content = build_close_bark_content(
            close_type=close_type,
            symbol=symbol,
            account_name=account['account_name'],
            close_results=close_result['close_results'],
            okx_resp=close_result['okx_resp'] if close_result['success'] else None,
            error_msg=None if close_result['success'] else close_result.get('error_msg', '平仓失败')
        )
        logger.info(f"准备发送Bark通知，参数如下：title={bark_title}, content={bark_content}")
        send_bark_notification(bark_title, bark_content)
        logger.info(f"Bark通知已发送: {bark_title}")

async def auto_restart_every_30min():
    while True:
        await asyncio.sleep(AUTO_RESTART_INTERVAL)  # 使用顶部变量
        logger.info(f'【自动重启】{AUTO_RESTART_INTERVAL//60}分钟到，准备重启进程...')
        os.execv(sys.executable, [sys.executable] + sys.argv)

async def send_startup_symbol_prices():
    symbols = ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    now = get_shanghai_time()
    for account in TEST_ACCOUNTS:
        account_name = account['account_name']
        price_lines = []
        for symbol in symbols:
            try:
                market_api = MarketData.MarketAPI(debug=False)
                response = market_api.get_ticker(instId=symbol)
                if response.get('code') == '0':
                    price = float(response['data'][0]['last'])
                    price_lines.append(f"{symbol}: {price}")
                else:
                    price_lines.append(f"{symbol}: 获取失败({response.get('msg', '')})")
            except Exception as e:
                price_lines.append(f"{symbol}: 获取异常({e})")
        log_msg = f"【启动价格播报】{now}\n账户: {account_name}\n" + "\n".join(price_lines)
        logger.info(log_msg)
        if TG_LOG_GROUP_ID:
            await client.send_message(TG_LOG_GROUP_ID, log_msg)

async def set_leverage_for_all_accounts():
    symbols = ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    now = get_shanghai_time()
    for account in TEST_ACCOUNTS:
        account_name = account['account_name']
        for symbol in symbols:
            # 杠杆倍数从环境变量读取，默认10
            leverage = os.getenv(f"OKX{account['account_idx']}_LEVERAGE", "10")
            print("读取到的杠杆：", leverage)
            try:
                result = set_account_leverage(
                    account['API_KEY'],
                    account['SECRET_KEY'],
                    account['PASSPHRASE'],
                    account['FLAG'],
                    symbol,
                    leverage,
                    mgn_mode="cross"
                )
                log_msg = f"【杠杆设置】{now}\n账户: {account_name}\n标的: {symbol}\n杠杆: {leverage}\n返回: {result}"
                logger.info(log_msg)
                if TG_LOG_GROUP_ID:
                    await client.send_message(TG_LOG_GROUP_ID, log_msg)
            except Exception as e:
                log_msg = f"【杠杆设置异常】{now}\n账户: {account_name}\n标的: {symbol}\n杠杆: {leverage}\n异常: {e}"
                logger.error(log_msg)
                if TG_LOG_GROUP_ID:
                    await client.send_message(TG_LOG_GROUP_ID, log_msg)

# ===== 启动时只执行一次的初始化动作 =====
# 1. 设置所有账户杠杆（只在程序启动/重启时执行一次，不会定时重复）
# 2. 推送启动时 BTC/ETH 价格
# 3. 初始化消息ID缓存
# =====================================

async def main():
    await client.start()
    logger.info(f'已登录 Telegram，监听频道: {CHANNEL_IDS}')

    # 启动时为所有账户设置杠杆（只执行一次）
    await set_leverage_for_all_accounts()

    # 启动时推送BTC/ETH价格（只执行一次）
    await send_startup_symbol_prices()

    # 初始化消息ID缓存（只执行一次）
    await init_processed_ids()

    # 启动消息遗漏检测定时任务（循环）
    asyncio.create_task(check_and_patch_missing_signals())

    # 启动定时重启任务（循环）
    asyncio.create_task(auto_restart_every_30min())

    @client.on(events.NewMessage(chats=CHANNEL_IDS))
    async def handler(event):
        msg = event.message.text or ''
        sender = await event.get_sender()
        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', '')
        sh_time = get_shanghai_time()
        channel_id = event.chat_id
        msg_id = event.id
        # 记录消息ID，避免重复
        if channel_id not in PROCESSED_MESSAGE_IDS:
            PROCESSED_MESSAGE_IDS[channel_id] = set()
        if msg_id not in PROCESSED_MESSAGE_IDS[channel_id]:
            PROCESSED_MESSAGE_IDS[channel_id].add(msg_id)
            save_processed_ids(PROCESSED_MESSAGE_IDS)
        # 统一日志内容
        base_log = f"【信号播报】\n时间: {sh_time}\n频道: {channel_id}\n用户: {sender_name}\n原始信息: {msg}"
        # 提取开仓信号
        action, symbol = extract_trade_info(msg)
        if action and symbol:
            for account in TEST_ACCOUNTS:
                judge_log = f"信号判断: 检测到开仓信号 {action} {symbol} (账户: {account['account_name']})"
                order_result = await place_okx_order(account, action, symbol, get_order_size(account['account_idx'], symbol) or 0)
                result_log = f"下单返回: {json.dumps(order_result, ensure_ascii=False)}"
                full_log = f"{base_log}\n{judge_log}\n{result_log}"
                logger.info(full_log)
                if TG_LOG_GROUP_ID:
                    await client.send_message(TG_LOG_GROUP_ID, full_log)
        # 提取平仓信号
        close_type, close_symbol = extract_close_signal(msg)
        if close_type and close_symbol:
            for account in TEST_ACCOUNTS:
                judge_log = f"信号判断: 检测到平仓信号 {close_type} {close_symbol} (账户: {account['account_name']})"
                close_result = await close_okx_position(account, close_symbol, close_type)
                result_log = f"平仓返回: {json.dumps(close_result, ensure_ascii=False)}"
                full_log = f"{base_log}\n{judge_log}\n{result_log}"
                logger.info(full_log)
                if TG_LOG_GROUP_ID:
                    await client.send_message(TG_LOG_GROUP_ID, full_log)

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())