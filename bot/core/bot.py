import asyncio
import json
import logging
import os
import random
import re
import sqlite3
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import pytz
import requests
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError

# 导入项目模块
from .config import get_config, update_config
from .db import update_status, get_status, log_message, get_logs, get_user, verify_password

# 设置日志
logger = logging.getLogger('tg_bot')


# 获取上海时间
def get_shanghai_time():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz)


# 生成订单ID
def generate_clord_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
    return f"TG{timestamp}{random_str}"[:32]


class TradingBot:
    def __init__(self):
        self.client = None
        self.running = False
        self.restart_interval = timedelta(hours=2)  # 2小时重启一次
        self.last_restart = datetime.now()
        self.phone_number = None
        self.api_id = None
        self.api_hash = None
        self.bark_api_key = None
        self.log_group_id = None
        self.proxy = None
        self.okx_config = None
        self.group_ids = None

    async def initialize(self):
        """初始化机器人，加载配置"""
        logger.info("初始化交易机器人...")

        # 加载Telegram配置
        telegram_config = get_config('telegram_config')
        self.phone_number = telegram_config['phone_number']
        self.api_id = telegram_config['api_id']
        self.api_hash = telegram_config['api_hash']
        self.bark_api_key = telegram_config['bark_api_key']
        self.log_group_id = telegram_config['log_group_id']

        # 加载代理配置（如果有）
        if 'proxy' in telegram_config:
            proxy_config = telegram_config['proxy']
            self.proxy = (proxy_config['protocol'], proxy_config['host'], proxy_config['port'])

        # 加载OKX配置
        self.okx_config = get_config('okx_config')

        # 加载监听群组
        self.group_ids = get_config('listen_groups')

        logger.info("配置加载完成")

    async def start(self):
        """启动机器人"""
        if self.running:
            logger.warning("机器人已经在运行中")
            return

        logger.info("启动交易机器人...")
        self.running = True

        try:
            # 创建Telegram客户端
            self.client = TelegramClient(
                f'session_{self.phone_number}',
                self.api_id,
                self.api_hash,
                proxy=self.proxy
            )

            # 注册事件处理
            @self.client.on(events.NewMessage(chats=self.group_ids))
            async def handler(event):
                await self.handle_message(event)

            # 连接并启动
            await self.client.start(self.phone_number)
            logger.info("Telegram客户端已启动")

            # 更新状态
            update_status('bot_status', 'running')

            # 发送启动通知
            shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
            start_message = f"🚀 交易机器人已启动\n时间: {shanghai_time}"
            await self.client.send_message(self.log_group_id, start_message)

            # 运行直到停止或重启
            start_time = datetime.now()
            while self.running:
                # 检查是否达到重启时间
                if datetime.now() - start_time >= self.restart_interval:
                    logger.info("达到重启时间，准备重启...")
                    await self.restart()
                    break

                # 等待一段时间再检查
                await asyncio.sleep(30)

        except (SessionPasswordNeededError, PhoneNumberInvalidError) as e:
            logger.error(f"登录Telegram失败: {e}")
            logger.error(traceback.format_exc())
            self.running = False
        except Exception as e:
            logger.error(f"启动机器人时出错: {e}")
            logger.error(traceback.format_exc())
            self.running = False

    async def stop(self):
        """停止机器人"""
        if not self.running:
            logger.warning("机器人未在运行")
            return

        logger.info("停止交易机器人...")
        self.running = False

        if self.client:
            await self.client.disconnect()
            self.client = None

        # 更新状态
        update_status('bot_status', 'stopped')

        # 发送停止通知
        shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
        stop_message = f"🛑 交易机器人已停止\n时间: {shanghai_time}"
        # 注意：此时客户端已断开，无法发送消息。如果需要，可以尝试重新连接发送，但通常停止时不发送。
        # 或者，我们可以在停止前发送。

    async def restart(self):
        """重启机器人"""
        logger.info("重启交易机器人...")
        await self.stop()
        # 等待2秒
        await asyncio.sleep(2)
        await self.start()

    async def handle_message(self, event):
        """处理收到的消息"""
        message_text = event.message.text
        shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
        group_id = event.chat_id

        logger.info(f"收到来自群组 {group_id} 的消息: {message_text[:100]}...")

        # 记录到日志群组
        base_log = f"时间: {shanghai_time}\n来源: 群组ID:{group_id}\n消息: {message_text[:300]}{'...' if len(message_text) > 300 else ''}"
        await self.client.send_message(self.log_group_id, f"📥 收到消息:\n{base_log}")

        # 提取交易信号
        action, symbol = self.extract_trade_info(message_text)
        if action and symbol:
            logger.info(f"检测到交易信号: {action} {symbol}")
            await self.process_trade_signal(action, symbol, base_log, shanghai_time)
        else:
            logger.info("未检测到交易信号")
            await self.client.send_message(self.log_group_id, f"📭 未检测到交易信号\n{base_log}")

    def extract_trade_info(self, message):
        """从消息中提取交易信息"""
        # 这里实现你的提取逻辑，例如使用正则表达式
        # 示例：匹配 "执行交易:做多" 和 "策略当前交易对:ETHUSDT.P"
        action_match = re.search(r"执行交易:(做多|做空)", message)
        symbol_match = re.search(r"策略当前交易对:(\w+)USDT\.P", message)

        if action_match and symbol_match:
            action = action_match.group(1)
            symbol = symbol_match.group(1)
            return action, symbol
        return None, None

    async def process_trade_signal(self, action, symbol, base_log, shanghai_time):
        """处理交易信号"""
        trade_log = f"✅ 检测到交易信号!\n{base_log}\n动作: {action}\n符号: {symbol}"
        await self.client.send_message(self.log_group_id, trade_log)

        # 发送Bark通知
        bark_message = f"时间: {shanghai_time}\n交易信号: {action} {symbol}"
        self.send_bark_notification("新的交易信号", bark_message)

        # 执行交易（这里简化，实际应调用下单函数）
        logger.info(f"执行交易: {action} {symbol}")
        # 注意：实际交易代码需要根据你的需求实现

        # 这里可以添加下单逻辑，并处理每个账户
        for account in self.okx_config['accounts']:
            logger.info(f"为账户 {account['account_name']} 下单")
            # 调用下单函数，例如：self.place_order(account, action, symbol)
            # 根据结果发送通知

    def send_bark_notification(self, title, message):
        """发送Bark通知"""
        if not self.bark_api_key:
            logger.warning("Bark API Key未配置，跳过通知")
            return

        bark_url = f"https://api.day.app/{self.bark_api_key}/{title}/{message}"
        try:
            response = requests.get(bark_url)
            if response.status_code == 200:
                logger.info("Bark通知发送成功")
            else:
                logger.warning(f"Bark通知发送失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"发送Bark通知时出错: {e}")
            logger.error(traceback.format_exc())

    # 下单函数（需要根据你的需求实现）
    def place_order(self, account, action, symbol):
        """在OKX上下单"""
        # 这里实现下单逻辑，使用OKX API
        pass