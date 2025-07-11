import os
from telethon.sync import TelegramClient

def get_env(name, required=True):
    value = os.getenv(name)
    if required and not value:
        print(f"[FATAL] 缺少环境变量: {name}")
        exit(1)
    return value

api_id_str = get_env('TG_API_ID')
if not api_id_str:
    print("[FATAL] TG_API_ID 必须设置")
    exit(1)
try:
    api_id = int(api_id_str)
except Exception:
    print("[FATAL] TG_API_ID 必须为整数")
    exit(1)

api_hash = get_env('TG_API_HASH')
if not api_hash:
    print("[FATAL] TG_API_HASH 必须设置")
    exit(1)
phone_number = get_env('TG_PHONE_NUMBER')
if not phone_number:
    print("[FATAL] TG_PHONE_NUMBER 必须设置")
    exit(1)
session_name = f'session_{phone_number}'

if __name__ == "__main__":
    with TelegramClient(session_name, api_id, api_hash) as client:
        client.start(phone=phone_number)
        print("Telegram 登录成功！") 