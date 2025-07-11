import os
import sys
import time
import asyncio
import logging
import re
from datetime import datetime, timedelta
from telethon.sync import TelegramClient
from telethon import events
from utils import get_shanghai_time, send_bark_notification

from dotenv import load_dotenv
load_dotenv('.env')
print("TG_API_ID from env:", os.getenv("TG_API_ID"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('tgBotV2')

SESSION_DIR = os.getenv('SESSION_DIR', './data/sessions')
os.makedirs(SESSION_DIR, exist_ok=True)

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
    coin = symbol.split('-')[0]
    env_name = f"OKX{account_idx}_FIXED_QTY_{coin}"
    val = os.getenv(env_name)
    if val:
        try:
            return float(val)
        except Exception:
            return None
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

async def fake_okx_order(account_idx, signal, entry_price, size):
    take_profit = entry_price * 1.01
    stop_loss = entry_price * (1 - 0.027)
    margin = round(entry_price * size * 0.1, 2)
    clOrdId = f"SIM{int(time.time())}{account_idx}"
    okx_resp = {"code": "0", "msg": "模拟下单成功"}
    return {
        "success": True,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        "margin": margin,
        "clOrdId": clOrdId,
        "okx_resp": okx_resp
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

async def process_open_signal(action, symbol, price):
    """处理开仓信号"""
    for account_idx in [1, 2]:
        size = get_order_size(account_idx, symbol)
        if not size:
            logger.warning(f"未配置账户{account_idx}的下单数量，跳过")
            continue
        entry_price = price
        order_result = await fake_okx_order(account_idx, {'symbol': symbol, 'action': action}, entry_price, size)
        bark_title = f"Tg信号策略{action}-{symbol}"
        bark_content = build_bark_content(
            signal={'symbol': symbol, 'action': action},
            account_name=f"OKX{account_idx}",
            entry_price=entry_price,
            size=size,
            margin=order_result['margin'],
            take_profit=order_result['take_profit'],
            stop_loss=order_result['stop_loss'],
            clOrdId=order_result['clOrdId'],
            okx_resp=order_result['okx_resp'] if order_result['success'] else None,
            error_msg=None if order_result['success'] else "下单失败"
        )
        send_bark_notification(bark_title, bark_content)
        logger.info(f"Bark通知已发送: {bark_title}")

async def process_close_signal(close_type, symbol):
    """处理平仓信号"""
    for account_idx in [1, 2]:
        close_result = await fake_close_position(account_idx, symbol, close_type)
        bark_title = f"Tg信号策略平仓-{symbol}"
        bark_content = build_close_bark_content(
            close_type=close_type,
            symbol=symbol,
            account_name=f"OKX{account_idx}",
            close_results=close_result['close_results'],
            okx_resp=close_result['okx_resp'] if close_result['success'] else None,
            error_msg=None if close_result['success'] else "平仓失败"
        )
        send_bark_notification(bark_title, bark_content)
        logger.info(f"Bark通知已发送: {bark_title}")

async def main():
    await client.start()
    logger.info(f'已登录 Telegram，监听频道: {CHANNEL_IDS}')

    @client.on(events.NewMessage(chats=CHANNEL_IDS))
    async def handler(event):
        msg = event.message.text or ''
        sender = await event.get_sender()
        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', '')
        sh_time = get_shanghai_time()
        log_msg = f"[{sh_time}] 来自频道{event.chat_id} 用户{sender_name} 消息: {msg[:100]}"
        logger.info(log_msg)
        if TG_LOG_GROUP_ID:
            await client.send_message(TG_LOG_GROUP_ID, log_msg)
        
        # 提取开仓信号
        action, symbol = extract_trade_info(msg)
        if action and symbol:
            logger.info(f"检测到开仓信号: {action} {symbol}")
            await process_open_signal(action, symbol, 0)  # 价格暂时设为0，实际应从信号中提取
        
        # 提取平仓信号
        close_type, close_symbol = extract_close_signal(msg)
        if close_type and close_symbol:
            logger.info(f"检测到平仓信号: {close_type} {close_symbol}")
            await process_close_signal(close_type, close_symbol)

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())