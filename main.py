import os
import sys
import requests
from telethon import TelegramClient, events
from datetime import datetime
import pytz

# 从环境变量读取配置
def get_env(name, required=True):
    value = os.getenv(name)
    if required and not value:
        print(f"[FATAL] 缺少环境变量: {name}")
        sys.exit(1)
    return value

api_id_str = get_env('TG_API_ID')
if not api_id_str:
    print("[FATAL] TG_API_ID 必须设置")
    sys.exit(1)
try:
    api_id = int(api_id_str)
except Exception:
    print("[FATAL] TG_API_ID 必须为整数")
    sys.exit(1)

api_hash = get_env('TG_API_HASH')
if not api_hash:
    print("[FATAL] TG_API_HASH 必须设置")
    sys.exit(1)
phone_number = get_env('TG_PHONE_NUMBER')
if not phone_number:
    print("[FATAL] TG_PHONE_NUMBER 必须设置")
    sys.exit(1)
log_group_id = get_env('TG_LOG_GROUP_ID', required=False)
bark_api_key = get_env('BARK_API_KEY', required=False)
session_name = f'session_{phone_number}'

group_ids_env = get_env('TG_GROUP_IDS')
if not group_ids_env:
    print("[FATAL] TG_GROUP_IDS 必须设置")
    sys.exit(1)
try:
    group_ids = [int(gid.strip()) for gid in group_ids_env.split(',') if gid.strip()]
except Exception:
    print("[FATAL] TG_GROUP_IDS 格式错误，必须为英文逗号分隔的群组ID列表")
    sys.exit(1)

if not group_ids:
    print("[FATAL] TG_GROUP_IDS 未配置监听群组ID，或内容为空")
    sys.exit(1)

# Bark 推送
def send_bark_notification(bark_api_key, message):
    bark_url = f"https://api.day.app/{bark_api_key}/"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'title': 'TG Signal',
        'body': message,
        'group': 'TG Signal',
    }
    try:
        response = requests.post(bark_url, headers=headers, data=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"发送 Bark 通知时出错: {e}")
        return False

if __name__ == "__main__":
    with TelegramClient(session_name, api_id, api_hash) as client:
        @client.on(events.NewMessage(chats=group_ids))
        async def handler(event):
            message_text = event.message.text
            shanghai_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
            chat = await event.get_chat()
            group_title = getattr(chat, 'title', '未知群组')
            group_id = getattr(chat, 'id', '未知ID')
            sender = await event.get_sender()
            sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', '未知用户')
            sender_id = getattr(sender, 'id', '未知ID')
            log_line = f"[{shanghai_time}] 群组: {group_title} (ID: {group_id}) | 发送者: {sender_name} (ID: {sender_id})\n消息: {message_text}\n"
            print(log_line)
            # 自动转发所有消息到日志群组
            if log_group_id:
                try:
                    await client.send_message(int(log_group_id), log_line)
                except Exception as e:
                    print(f"转发到日志群组失败: {e}")
            # 检测交易信号并Bark推送
            if '交易' in message_text or 'signal' in message_text.lower():
                bark_message = f"时间: {shanghai_time}\n群组: {group_title}\n消息: {message_text}"
                if bark_api_key:
                    if send_bark_notification(bark_api_key, bark_message):
                        print("Bark 通知发送成功！")
                    else:
                        print("Bark 通知发送失败！")
        print(f"开始监听群组 IDs: {group_ids}")
        client.run_until_disconnected() 