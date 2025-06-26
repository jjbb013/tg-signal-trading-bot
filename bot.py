import asyncio
from telethon.sync import TelegramClient
from telethon import events
from datetime import datetime
import pytz
import requests
import re

class BotManager:
    def __init__(self, config, groups, log_callback):
        self.config = config
        self.groups = groups
        self.log_callback = log_callback
        self.client = None
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        asyncio.run(self._run())

    def stop(self):
        if self.client:
            self.client.disconnect()
        self.running = False

    async def _run(self):
        proxy = None
        if self.config.proxy_protocol and self.config.proxy_host and self.config.proxy_port:
            proxy = (self.config.proxy_protocol, self.config.proxy_host, int(self.config.proxy_port))
        client_args = {
            'session': f'session_{self.config.phone_number}',
            'api_id': self.config.api_id,
            'api_hash': self.config.api_hash
        }
        if proxy:
            client_args['proxy'] = proxy
        group_id_list = [int(g.group_id) for g in self.groups]
        async with TelegramClient(**client_args) as client:
            # 检查 session 是否已登录
            if not await client.is_user_authorized():
                raise Exception('Session 未登录，请先在网页端完成登录')
            @client.on(events.NewMessage(chats=group_id_list))
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
                self.log_callback(log_line)
                # 交易信号提取
                trade_pattern = r"执行交易:(.+?)(?=\n=+|$)"
                trade_match = re.search(trade_pattern, message_text)
                if trade_match:
                    trade_info = trade_match.group(1).strip()
                    log_message = f"时间: {shanghai_time}, 交易信号: {trade_info}"
                    self.log_callback(f"检测到交易信号并提取时间: {log_message}")
                    # 发送 Bark 通知
                    if self.config.bark_api_key:
                        bark_url = f"https://api.day.app/{self.config.bark_api_key}/"
                        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                        payload = {
                            'title': 'TG Signal',
                            'body': f"时间: {shanghai_time}\n交易信号: {trade_info}",
                            'group': 'TG Signal',
                        }
                        try:
                            requests.post(bark_url, headers=headers, data=payload)
                        except Exception as e:
                            self.log_callback(f"Bark 通知发送失败: {e}")
                    # 发送到日志群组
                    try:
                        await client.send_message(self.config.log_group_id, log_message)
                    except Exception as e:
                        self.log_callback(f"发送到日志群组失败: {e}")
            await client.run_until_disconnected() 