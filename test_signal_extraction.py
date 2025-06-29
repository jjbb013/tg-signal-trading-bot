#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def extract_trade_info(message):
    """提取交易信息"""
    print(f"正在从消息中提取交易信息: {message[:100]}...")
    
    # 首先检查是否包含平仓关键词，如果是平仓信号则不提取开仓信息
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if has_close_signal:
        print("检测到平仓信号，跳过开仓信号提取")
        return None, None
    
    action_pattern = r"执行交易:(.+?)(?= \d+\.\d+\w+)"
    action_match = re.search(action_pattern, message)
    symbol_pattern = r"策略当前交易对:(\w+USDT\.P)"
    symbol_match = re.search(symbol_pattern, message)
    if action_match and symbol_match:
        action = action_match.group(1).strip()
        symbol = symbol_match.group(1).split('USDT')[0]
        print(f"成功提取交易信息 - 动作: {action}, 符号: {symbol}")
        return action, symbol
    else:
        print("无法从消息中提取交易信息")
        return None, None

def extract_close_signal(message):
    """提取平仓信号"""
    print(f"正在从消息中提取平仓信号: {message[:100]}...")
    
    # 检查是否包含平仓关键词
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if not has_close_signal:
        return None, None
    
    # 提取交易对信息
    symbol_pattern = r"策略当前交易对:(\w+USDT\.P)"
    symbol_match = re.search(symbol_pattern, message)
    
    if symbol_match:
        symbol = symbol_match.group(1).split('USDT')[0]
        # 确定平仓类型
        if '空止盈' in message or '空止损' in message:
            close_type = 'short'
        elif '多止盈' in message or '多止损' in message:
            close_type = 'long'
        else:
            close_type = 'both'
        
        print(f"成功提取平仓信号 - 类型: {close_type}, 符号: {symbol}")
        return close_type, symbol
    else:
        print("无法从平仓信号中提取交易对信息")
        return None, None

# 测试消息
test_message = """币coin："BTC2023"实盘："量化策略F"
===========================
策略当前交易对:ETHUSDT.P
==========================
ETH价格:2443.38
===========================
执行交易:多止盈 0.072ETH"""

test_message2 = """币coin："BTC2023"实盘："量化策略F"
===========================
策略当前交易对:ETHUSDT.P
==========================
ETH价格:2443.38
===========================
执行交易:做多 0.072ETH"""

print("=" * 50)
print("测试消息1 (平仓信号):")
print(test_message)
print("=" * 50)

# 测试信号提取
print("\n1. 测试开仓信号提取:")
action, symbol = extract_trade_info(test_message)
print(f"结果: action={action}, symbol={symbol}")

print("\n2. 测试平仓信号提取:")
close_type, close_symbol = extract_close_signal(test_message)
print(f"结果: close_type={close_type}, close_symbol={close_symbol}")

print("\n3. 判断信号类型:")
if action and symbol:
    print("✅ 检测到开仓信号")
elif close_type and close_symbol:
    print("🔄 检测到平仓信号")
else:
    print("📭 未检测到任何信号")

print("\n" + "=" * 50)
print("测试消息2 (开仓信号):")
print(test_message2)
print("=" * 50)

# 测试信号提取
print("\n1. 测试开仓信号提取:")
action2, symbol2 = extract_trade_info(test_message2)
print(f"结果: action={action2}, symbol={symbol2}")

print("\n2. 测试平仓信号提取:")
close_type2, close_symbol2 = extract_close_signal(test_message2)
print(f"结果: close_type={close_type2}, close_symbol={close_symbol2}")

print("\n3. 判断信号类型:")
if action2 and symbol2:
    print("✅ 检测到开仓信号")
elif close_type2 and close_symbol2:
    print("🔄 检测到平仓信号")
else:
    print("📭 未检测到任何信号") 