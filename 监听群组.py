from telethon.sync import TelegramClient
import json
import requests
from telethon import events
import re
from datetime import datetime
import pytz

def load_config():
    """加载配置文件"""
    try:
        with open('telegram_config.json', 'r') as config_file:
            config = json.load(config_file)
            return config
    except FileNotFoundError:
        print("配置文件 telegram_config.json 未找到！")
        exit(1)
    except json.JSONDecodeError:
        print("配置文件格式错误！")
        exit(1)

def load_listen_groups():
    """加载要监听的群组 IDs"""
    try:
        with open('listen_group.txt', 'r') as group_file:
            group_ids = []
            for line in group_file:
                if 'ID:' in line:
                    group_id = int(line.split('ID: ')[1])
                    group_ids.append(group_id)
            if not group_ids:
                print("listen_groups.txt 文件中没有找到有效的群组 ID！")
                exit(1)
            return group_ids
    except FileNotFoundError:
        print("listen_groups.txt 文件未找到！")
        exit(1)

def send_bark_notification(bark_api_key, message):
    """发送 Bark 通知"""
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

def extract_trade_info(message):
    """从消息中提取交易信息"""
    trade_pattern = r"执行交易:(.+?)(?=\n=+|$)"
    trade_match = re.search(trade_pattern, message)
    if trade_match:
        return trade_match.group(1).strip()
    else:
        return None

def get_shanghai_time():
    """获取当前上海时间"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz).strftime('%Y-%m-%d %H:%M:%S')

def main():
    # 加载配置文件
    config = load_config()
    api_id = config['api_id']
    api_hash = config['api_hash']
    phone_number = config['phone_number']
    bark_api_key = config['bark_api_key']
    log_group_id = config['log_group_id']

    # 加载代理配置
    proxy_config = config.get('proxy', None)
    proxy = None
    if proxy_config:
        proxy = (proxy_config['protocol'], proxy_config['host'], proxy_config['port'])

    # 加载监听群组 IDs
    group_ids = load_listen_groups()

    # 创建客户端实例
    client_args = {
        'session': f'session_{phone_number}',
        'api_id': api_id,
        'api_hash': api_hash
    }
    if proxy:
        client_args['proxy'] = proxy

    with TelegramClient(**client_args) as client:
        @client.on(events.NewMessage(chats=group_ids))
        async def handler(event):
            message_text = event.message.text
            shanghai_time = get_shanghai_time()
            # 获取群组信息
            chat = await event.get_chat()
            group_title = getattr(chat, 'title', '未知群组')
            group_id = getattr(chat, 'id', '未知ID')
            # 获取发送者信息
            sender = await event.get_sender()
            sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', '未知用户')
            sender_id = getattr(sender, 'id', '未知ID')
            # 构建日志内容
            log_line = f"[{shanghai_time}] 群组: {group_title} (ID: {group_id}) | 发送者: {sender_name} (ID: {sender_id})\n消息: {message_text}\n"
            # 输出到控制台
            print(log_line)
            # 记录到本地日志
            with open('listen_log.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(log_line)

            trade_info = extract_trade_info(message_text)
            if trade_info:
                log_message = f"时间: {shanghai_time}, 交易信号: {trade_info}"
                print(f"检测到交易信号并提取时间: {log_message}")
                try:
                    # 发送交易信号到日志记录群组
                    await client.send_message(log_group_id, log_message)
                    print("交易信号已发送到日志记录群组！")
                    # 发送 Bark 通知
                    bark_message = f"时间: {shanghai_time}\n交易信号: {trade_info}"
                    if send_bark_notification(bark_api_key, bark_message):
                        print("Bark 通知发送成功！")
                    else:
                        print("Bark 通知发送失败！")
                except Exception as e:
                    print(f"发送交易信号或 Bark 通知时出错: {e}")

        print(f"开始监听群组 IDs: {group_ids}")
        client.run_until_disconnected()

if __name__ == "__main__":
    main()