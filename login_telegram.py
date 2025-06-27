#!/usr/bin/env python3
"""
Telegram 登录脚本
使用方法：
1. 确保已配置 telegram_config.json
2. 运行: python login_telegram.py
3. 按照提示输入手机号、验证码和密码
"""

import json
import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

def load_config():
    """加载配置文件"""
    if not os.path.exists("telegram_config.json"):
        print("❌ 错误: 找不到 telegram_config.json 配置文件")
        print("请先创建配置文件，包含以下内容:")
        print("""
{
    "api_id": "你的API_ID",
    "api_hash": "你的API_HASH",
    "phone_number": "你的手机号",
    "bark_api_key": "Bark推送密钥",
    "log_group_id": "日志群组ID"
}
        """)
        return None
    
    with open("telegram_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    required_fields = ["api_id", "api_hash", "phone_number"]
    for field in required_fields:
        if not config.get(field):
            print(f"❌ 错误: 配置文件中缺少 {field}")
            return None
    
    return config

async def login_telegram():
    """Telegram登录流程"""
    config = load_config()
    if not config:
        return False
    
    print("🤖 Telegram 登录工具")
    print("=" * 50)
    
    # 创建客户端
    session_name = f"session_{config['phone_number']}"
    client = TelegramClient(session_name, config['api_id'], config['api_hash'])
    
    try:
        print(f"📱 正在连接到 Telegram...")
        await client.connect()
        
        # 检查是否已经登录
        if await client.is_user_authorized():
            print("✅ 已经登录，无需重新登录")
            await client.disconnect()
            return True
        
        # 开始登录流程
        print(f"📞 手机号: {config['phone_number']}")
        phone = input("请输入手机号 (直接回车使用配置文件中的号码): ").strip()
        if not phone:
            phone = config['phone_number']
        
        print(f"📤 正在发送验证码到 {phone}...")
        await client.send_code_request(phone)
        
        # 输入验证码
        while True:
            code = input("📱 请输入收到的验证码: ").strip()
            if not code:
                print("❌ 验证码不能为空")
                continue
            
            try:
                await client.sign_in(phone, code)
                break
            except PhoneCodeInvalidError:
                print("❌ 验证码错误，请重新输入")
                continue
            except SessionPasswordNeededError:
                print("🔐 需要两步验证密码")
                break
            except Exception as e:
                print(f"❌ 登录失败: {e}")
                return False
        
        # 检查是否需要两步验证
        if not await client.is_user_authorized():
            while True:
                password = input("🔐 请输入两步验证密码: ").strip()
                if not password:
                    print("❌ 密码不能为空")
                    continue
                
                try:
                    await client.sign_in(password=password)
                    break
                except Exception as e:
                    print(f"❌ 密码错误: {e}")
                    continue
        
        # 验证登录成功
        if await client.is_user_authorized():
            print("✅ 登录成功！")
            me = await client.get_me()
            print(f"👤 用户: {me.first_name} (@{me.username})")
            print(f"📱 手机号: {me.phone}")
            print(f"🆔 用户ID: {me.id}")
            return True
        else:
            print("❌ 登录失败")
            return False
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    finally:
        await client.disconnect()

def main():
    """主函数"""
    print("🚀 启动 Telegram 登录工具...")
    
    try:
        result = asyncio.run(login_telegram())
        if result:
            print("\n🎉 登录完成！现在可以启动监听机器人了")
            print("💡 提示: 运行 python main.py 启动Web界面")
        else:
            print("\n❌ 登录失败，请检查配置和网络连接")
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户取消操作")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")

if __name__ == "__main__":
    main() 