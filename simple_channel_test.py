#!/usr/bin/env python3
"""
简化的频道监听测试脚本
专门用于测试特定频道的消息监听
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from telethon.sync import TelegramClient
from telethon import events
import pytz

# 设置日志
def setup_logger():
    """设置日志"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = f'logs/simple_channel_test_{current_date}.log'
    
    logger = logging.getLogger('channel_test')
    logger.setLevel(logging.DEBUG)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 加载配置
def load_config():
    """加载配置文件"""
    try:
        with open('telegram_config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        sys.exit(1)

def get_shanghai_time():
    """获取上海时间"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(shanghai_tz)

class SimpleChannelTester:
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger()
        self.client = None
        self.target_channel_id = -1001638841860  # 目标频道ID
        self.message_count = 0
        self.all_messages = []
        
    async def setup_client(self):
        """设置Telegram客户端"""
        try:
            # 创建客户端
            self.client = TelegramClient(
                f'session_test_{self.config["phone_number"]}',
                self.config['api_id'],
                self.config['api_hash'],
                connection_retries=5,
                timeout=30
            )
            
            self.client.start()
            self.logger.info("Telegram客户端连接成功")
            
        except Exception as e:
            self.logger.error(f"设置客户端失败: {e}")
            raise
    
    async def test_channel_access(self):
        """测试频道访问"""
        try:
            self.logger.info(f"测试频道访问: {self.target_channel_id}")
            
            # 获取频道信息
            channel = self.client.get_entity(self.target_channel_id)
            self.logger.info(f"频道信息: {channel}")
            
            # 获取最近消息
            messages = []
            for message in self.client.iter_messages(channel, limit=5):
                if message and message.text:
                    messages.append({
                        'id': message.id,
                        'date': str(message.date) if message.date else None,
                        'text': message.text[:100],
                        'sender_id': message.sender_id
                    })
            
            self.logger.info(f"最近5条消息: {json.dumps(messages, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"测试频道访问失败: {e}")
    
    async def setup_listeners(self):
        """设置监听器"""
        
        # 监听所有消息
        @self.client.on(events.NewMessage())
        async def all_messages_handler(event):
            """监听所有消息"""
            try:
                shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取聊天信息
                chat = event.get_chat()
                chat_title = getattr(chat, 'title', f"ChatID:{event.chat_id}")
                
                # 记录消息
                message_info = {
                    'timestamp': shanghai_time,
                    'chat_id': event.chat_id,
                    'chat_title': chat_title,
                    'message_id': event.id,
                    'sender_id': event.sender_id,
                    'text_length': len(event.message.text) if event.message and event.message.text else 0,
                    'text_preview': event.message.text[:100] if event.message and event.message.text else "No text"
                }
                
                self.logger.info(f"收到消息: {json.dumps(message_info, ensure_ascii=False)}")
                
                # 如果是目标频道
                if event.chat_id == self.target_channel_id:
                    self.message_count += 1
                    self.logger.info(f"✅ 目标频道消息 #{self.message_count}: {event.message.text[:200]}")
                    
                    # 保存消息
                    self.all_messages.append({
                        'timestamp': shanghai_time,
                        'message_id': event.id,
                        'text': event.message.text,
                        'sender_id': event.sender_id
                    })
                
            except Exception as e:
                self.logger.error(f"处理消息失败: {e}")
        
        # 监听特定频道消息
        @self.client.on(events.NewMessage(chats=[self.target_channel_id]))
        async def target_channel_handler(event):
            """监听目标频道消息"""
            try:
                shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
                self.logger.info(f"🎯 目标频道监听器收到消息: {shanghai_time}")
                self.logger.info(f"消息ID: {event.id}, 内容: {event.message.text[:200]}")
                
            except Exception as e:
                self.logger.error(f"目标频道监听器失败: {e}")
    
    async def periodic_history_check(self):
        """定期检查历史消息"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                shanghai_time = get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')
                self.logger.info(f"🕐 定期检查历史消息: {shanghai_time}")
                
                # 获取最近的消息
                channel = self.client.get_entity(self.target_channel_id)
                recent_messages = []
                
                for message in self.client.iter_messages(channel, limit=10):
                    if message and message.text:
                        recent_messages.append({
                            'id': message.id,
                            'date': str(message.date) if message.date else None,
                            'text': message.text[:100]
                        })
                
                self.logger.info(f"历史消息检查结果: {len(recent_messages)} 条消息")
                for msg in recent_messages:
                    self.logger.info(f"历史消息: {json.dumps(msg, ensure_ascii=False)}")
                
                # 检查是否有遗漏的消息
                if self.all_messages:
                    latest_realtime_id = max(msg['message_id'] for msg in self.all_messages)
                    latest_history_id = max(msg['id'] for msg in recent_messages)
                    
                    if latest_history_id > latest_realtime_id:
                        self.logger.warning(f"发现遗漏消息! 历史最新ID: {latest_history_id}, 实时最新ID: {latest_realtime_id}")
                
            except Exception as e:
                self.logger.error(f"定期检查失败: {e}")
    
    async def run_test(self):
        """运行测试"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("开始频道监听测试")
            self.logger.info(f"目标频道ID: {self.target_channel_id}")
            self.logger.info(f"开始时间: {get_shanghai_time().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 60)
            
            # 设置客户端
            await self.setup_client()
            
            # 测试频道访问
            await self.test_channel_access()
            
            # 设置监听器
            await self.setup_listeners()
            
            # 启动定期检查
            asyncio.create_task(self.periodic_history_check())
            
            self.logger.info("所有监听器已设置，开始监听...")
            self.logger.info("按 Ctrl+C 停止测试")
            
            # 保持运行
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止...")
            self.logger.info(f"总共收到 {self.message_count} 条目标频道消息")
        except Exception as e:
            self.logger.error(f"测试过程中出错: {e}")
        finally:
            if self.client:
                self.client.disconnect()
            self.logger.info("测试结束")

async def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 创建测试器
    tester = SimpleChannelTester(config)
    
    # 运行测试
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main()) 