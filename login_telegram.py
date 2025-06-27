from telethon.sync import TelegramClient
import json

with open('telegram_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

api_id = config['api_id']
api_hash = config['api_hash']
phone_number = config['phone_number']
session_name = f'session_{phone_number}'

if __name__ == "__main__":
    with TelegramClient(session_name, api_id, api_hash) as client:
        client.start(phone=phone_number)
        print("Telegram 登录成功！") 