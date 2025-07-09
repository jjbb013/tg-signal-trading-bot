"""
任务名称
name: OKX UTILS 工具
定时规则
cron: 1 1 1 1 *
"""
import os
import json
import random
from re import T
import string
import time
from datetime import datetime, timezone, timedelta
import okx.MarketData as MarketData
import okx.Trade as Trade
import requests

# ========== 环境与配置 ==========
IS_DEVELOPMENT = True
# try:
#     from config_local import *
#     IS_DEVELOPMENT = True
# except ImportError:
#     IS_DEVELOPMENT = False



# ========== 1. 获取上海时区时间 ==========
def get_shanghai_time(fmt="%Y-%m-%d %H:%M:%S"):
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime(fmt)

# ========== 2. 获取环境变量 ==========
def get_env_var(var_name, suffix="", default=None):
    # 优先从 os.environ 获取，保证全局一致
    val = os.environ.get(f"{var_name}{suffix}")
    if val is not None:
        return val
    # 兼容老逻辑（globals）
    if IS_DEVELOPMENT:
        try:
            return globals()[f"{var_name}{suffix}"]
        except KeyError:
            return default
    else:
        return default

# ========== 3. 获取未成交订单 ==========
def get_orders_pending(trade_api, inst_id, max_retries=3, retry_delay=2, account_prefix=""):
    for attempt in range(max_retries + 1):
        try:
            result = trade_api.get_order_list(instId=inst_id, state="live")
            print(f"[get_orders_pending][{get_shanghai_time()}] HTTP返回: {json.dumps(result, ensure_ascii=False)}")
            if result and 'code' in result and result['code'] == '0' and 'data' in result:
                return result['data']
        except Exception as e:
            print(f"[get_orders_pending][{get_shanghai_time()}] 异常: {e}")
        if attempt < max_retries:
            time.sleep(retry_delay)
    return []

# ========== 4. 批量撤销开仓订单 ==========
def cancel_pending_open_orders(trade_api, inst_id, order_ids=None, max_retries=3, retry_delay=2, account_prefix=""):
    """
    支持传入 order_ids（单个或列表），否则自动查找当前挂单。
    """
    if order_ids is not None:
        if isinstance(order_ids, str):
            order_ids = [order_ids]
        cancel_orders = [{"instId": inst_id, "ordId": oid} for oid in order_ids]
    else:
        orders = get_orders_pending(trade_api, inst_id, max_retries, retry_delay, account_prefix)
        cancel_orders = []
        for order in orders:
            if order.get('ordType') == 'limit' and ((order.get('side') == 'buy' and order.get('posSide') == 'long') or (order.get('side') == 'sell' and order.get('posSide') == 'short')):
                cancel_orders.append({"instId": inst_id, "ordId": order['ordId']})
    if not cancel_orders:
        print("[cancel_pending_open_orders] 没有可撤销的订单")
        return False
    for attempt in range(max_retries + 1):
        try:
            result = trade_api.cancel_multiple_orders(cancel_orders)
            print(f"[cancel_pending_open_orders] 撤单接口返回: {result}")
            if result and 'code' in result and result['code'] == '0':
                return True
        except Exception as e:
            print(f"[cancel_pending_open_orders] 撤单异常: {e}")
        if attempt < max_retries:
            time.sleep(retry_delay)
    return False

# ========== 5. 生成clOrdId ==========
def generate_clord_id(prefix="ORD"):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"{prefix}{timestamp}{rand}"[:32]

# ========== 6. 构建下单参数 ==========
def build_order_params(inst_id, side, entry_price, size, pos_side, take_profit, stop_loss, prefix="ORD"):
    cl_ord_id = generate_clord_id(prefix)
    attach_algo_ord = {
        "attachAlgoClOrdId": generate_clord_id(prefix),
        "tpTriggerPx": str(take_profit),
        "tpOrdPx": "-1",
        "tpOrdKind": "condition",
        "slTriggerPx": str(stop_loss),
        "slOrdPx": "-1",
        "tpTriggerPxType": "last",
        "slTriggerPxType": "last"
    }
    return {
        "instId": inst_id,
        "tdMode": "cross",
        "side": side,
        "ordType": "limit",
        "px": str(entry_price),
        "sz": str(size),
        "clOrdId": cl_ord_id,
        "posSide": pos_side,
        "attachAlgoOrds": [attach_algo_ord]
    }

# ========== 7. Bark通知格式 ==========
def send_bark_notification(title, content, group=None):
    bark_key = os.getenv("BARK_KEY")
    bark_group = group or os.getenv("BARK_GROUP", "未配置的GROUP")
    if not bark_key:
        print("[WARN] 未配置BARK_KEY，无法发送Bark通知")
        return
    # 支持直接填URL或只填key
    if bark_key.startswith("http"):
        url = bark_key
    else:
        url = f"https://api.day.app/{bark_key}"
    # 尝试POST json
    try:
        resp = requests.post(url, json={"title": title, "body": content, "group": bark_group}, timeout=10)
        print(f"[Bark通知] 状态码: {resp.status_code}, 响应: {resp.text[:100]}")
        if resp.status_code == 200:
            return
    except Exception as e:
        print(f"[Bark通知] POST失败: {e}")
    # 兼容GET方式
    try:
        import urllib.parse
        params = urllib.parse.urlencode({"title": title, "body": content, "group": bark_group})
        resp = requests.get(f"{url}/{title}/{content}?group={bark_group}", timeout=10)
        print(f"[Bark通知] GET状态码: {resp.status_code}, 响应: {resp.text[:100]}")
    except Exception as e:
        print(f"[Bark通知] GET失败: {e}")

# ========== 8. 初始化交易API ==========
def init_trade_api(api_key, secret_key, passphrase, flag=None, suffix=""):
    if flag is None:
        flag = get_env_var("OKX_FLAG", suffix, "0")
    return Trade.TradeAPI(str(api_key), str(secret_key), str(passphrase), False, str(flag))

# ========== 新增：标准化获取 TradeAPI/AccountAPI ==========
def get_trade_api():
    api_key = get_env_var("OKX_API_KEY")
    secret_key = get_env_var("OKX_SECRET_KEY")
    passphrase = get_env_var("OKX_PASSPHRASE")
    flag = get_env_var("OKX_FLAG", default="0")
    return Trade.TradeAPI(str(api_key), str(secret_key), str(passphrase), False, str(flag))

def get_account_api():
    api_key = get_env_var("OKX_API_KEY")
    secret_key = get_env_var("OKX_SECRET_KEY")
    passphrase = get_env_var("OKX_PASSPHRASE")
    flag = get_env_var("OKX_FLAG", default="0")
    import okx.Account as Account
    return Account.AccountAPI(str(api_key), str(secret_key), str(passphrase), False, str(flag))

# ========== 9. 获取K线数据 ==========
def get_kline_data(api_key, secret_key, passphrase, inst_id, bar, limit=None, flag=None, suffix="", max_retries=3, retry_delay=2):
    if limit is None:
        limit = int(get_env_var("OKX_KLINE_LIMIT", suffix, 2))
    try:
        flag_str = str(flag) if flag is not None else "0"
        market_api = MarketData.MarketAPI(str(api_key), str(secret_key), str(passphrase), False, flag_str)
        print(f"[okx_utils] [MARKET] K线API初始化成功")
    except Exception as e:
        print(f"[okx_utils] [ERROR] K线API初始化失败: {str(e)}")
        return None
    for attempt in range(max_retries + 1):
        try:
            result = market_api.get_candlesticks(instId=inst_id, bar=bar, limit=str(limit))
            print(f"[DEBUG] K线原始返回: {result}")
            if result and 'data' in result and len(result['data']) >= 2:
                return result['data']
        except Exception as e:
            print(f"[okx_utils] [ERROR] 获取K线失败: {e}")
        if attempt < max_retries:
            time.sleep(retry_delay)
    return None 
