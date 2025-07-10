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

def parse_signal(msg: str):
    result = {
        "strategy": None,
        "symbol": None,
        "price": None,
        "action": None
    }
    # 策略名
    m = re.search(r"^(.*?)\n=+", msg)
    if m:
        result["strategy"] = m.group(1).strip()
    # 标的（更宽松，匹配冒号后所有非换行内容）
    m = re.search(r"策略当前交易对[:：]?([A-Z0-9\\.]+)", msg)
    if m:
        raw = m.group(1).strip()
        # 只给了单字母时，尝试用策略名补全
        if len(raw) <= 3 and result["strategy"]:
            coin = result["strategy"].split('-')[-1].replace('策略', '').replace(' ', '').upper()
            result["symbol"] = f"{coin}-USDT-SWAP"
        elif 'USDT.P' in raw:
            coin = raw.replace('USDT.P', '')
            result["symbol"] = f"{coin}-USDT-SWAP"
        else:
            result["symbol"] = f"{raw}-USDT-SWAP"
    # 价格
    m = re.search(r"([A-Z]+)价格[:：]?([0-9.]+)", msg)
    if m:
        try:
            result["price"] = float(m.group(2))
        except Exception:
            result["price"] = None
    # 动作（完整匹配多止盈/多止损/空止盈/空止损/多开仓/空开仓/平多/平空）
    m = re.search(r"执行交易[:：]?(多止盈|多止损|空止盈|空止损|多开仓|空开仓|平多|平空)", msg)
    if m:
        result["action"] = m.group(1)
    return result

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

async def process_signal(signal):
    for account_idx in [1, 2]:
        size = get_order_size(account_idx, signal['symbol'])
        if not size:
            logger.warning(f"未配置账户{account_idx}的下单数量，跳过")
            continue
        entry_price = signal['price']
        order_result = await fake_okx_order(account_idx, signal, entry_price, size)
        bark_title = f"Tg信号策略{signal['action']}-{signal['symbol']}"
        bark_content = build_bark_content(
            signal=signal,
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
        signal = parse_signal(msg)
        logger.info(f"信号解析结果: {signal}")
        if signal['symbol'] and signal['price'] and signal['action']:
            await process_signal(signal)

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())