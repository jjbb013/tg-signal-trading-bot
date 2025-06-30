#!/usr/bin/env python3
"""
测试正则表达式是否能正确匹配交易信号
"""

import re

def extract_trade_info(message):
    """测试版本的交易信号提取函数"""
    print(f"正在从消息中提取交易信息: {message[:100]}...")
    
    # 做多信号 - 支持多种格式
    long_patterns = [
        r'做多\s*([A-Z]+)',  # 做多 ETH
        r'([A-Z]+)\s*做多',  # ETH 做多
        r'买入\s*([A-Z]+)',  # 买入 ETH
        r'([A-Z]+)\s*买入',  # ETH 买入
        r'LONG\s*([A-Z]+)',  # LONG ETH
        r'([A-Z]+)\s*LONG',  # ETH LONG
        r'做多\s*\d+\.?\d*([A-Z]+)',  # 做多 0.072ETH
        r'([A-Z]+)\s*做多\s*\d+\.?\d*',  # ETH 做多 0.072
        r'买入\s*\d+\.?\d*([A-Z]+)',  # 买入 0.072ETH
        r'([A-Z]+)\s*买入\s*\d+\.?\d*',  # ETH 买入 0.072
    ]
    
    # 做空信号 - 支持多种格式
    short_patterns = [
        r'做空\s*([A-Z]+)',  # 做空 ETH
        r'([A-Z]+)\s*做空',  # ETH 做空
        r'卖出\s*([A-Z]+)',  # 卖出 ETH
        r'([A-Z]+)\s*卖出',  # ETH 卖出
        r'SHORT\s*([A-Z]+)',  # SHORT ETH
        r'([A-Z]+)\s*SHORT',  # ETH SHORT
        r'做空\s*\d+\.?\d*([A-Z]+)',  # 做空 0.072ETH
        r'([A-Z]+)\s*做空\s*\d+\.?\d*',  # ETH 做空 0.072
        r'卖出\s*\d+\.?\d*([A-Z]+)',  # 卖出 0.072ETH
        r'([A-Z]+)\s*卖出\s*\d+\.?\d*',  # ETH 卖出 0.072
    ]
    
    # 检查做多信号
    for i, pattern in enumerate(long_patterns):
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            print(f"✅ 检测到做多信号: {symbol} (模式 {i+1}: {pattern})")
            return '做多', symbol
    
    # 检查做空信号
    for i, pattern in enumerate(short_patterns):
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            print(f"✅ 检测到做空信号: {symbol} (模式 {i+1}: {pattern})")
            return '做空', symbol
    
    print("❌ 未检测到交易信号")
    return None, None

# 测试消息
test_messages = [
    "策略当前交易对:ETHUSDT.P\n==========================\nETH价格:2435.10\n===========================\n执行交易:做空 0.072ETH\n===========================",
    "做多 ETH",
    "ETH 做多",
    "做空 0.072ETH",
    "ETH 做空 0.072",
    "买入 BTC",
    "BTC 买入 0.001",
    "LONG ETH",
    "SHORT BTC"
]

print("=== 正则表达式测试 ===")
for i, message in enumerate(test_messages, 1):
    print(f"\n--- 测试消息 {i} ---")
    print(f"消息: {message}")
    action, symbol = extract_trade_info(message)
    if action and symbol:
        print(f"结果: {action} {symbol}")
    else:
        print("结果: 未匹配")
    print("-" * 50) 