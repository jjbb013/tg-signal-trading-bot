#!/usr/bin/env python3
"""
测试新的交易信号提取函数
"""

import re

def extract_trade_info(message):
    """从消息中提取交易信息"""
    print(f"正在从消息中提取交易信息: {message[:100]}...")
    
    # 首先检查是否包含平仓关键词，如果是平仓信号则不提取开仓信息
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if has_close_signal:
        print("检测到平仓信号，跳过开仓信号提取")
        return None, None
    
    # 尝试从标准格式中提取
    action_pattern = r"执行交易:(.+?)(?= \d+\.\d+\w+)"
    action_match = re.search(action_pattern, message)
    symbol_pattern = r"策略当前交易对:(\w+USDT\.P)"
    symbol_match = re.search(symbol_pattern, message)
    
    if action_match and symbol_match:
        action = action_match.group(1).strip()
        symbol = symbol_match.group(1).split('USDT')[0]
        print(f"成功提取交易信息 - 动作: {action}, 符号: {symbol}")
        return action, symbol
    
    # 如果标准格式不匹配，使用通用正则表达式
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
    for pattern in long_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            print(f"检测到做多信号: {symbol}")
            return '做多', symbol
    
    # 检查做空信号
    for pattern in short_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            symbol = match.group(1)
            print(f"检测到做空信号: {symbol}")
            return '做空', symbol
    
    print("未检测到交易信号")
    return None, None

def extract_close_signal(message):
    """提取平仓信号"""
    print(f"正在从消息中提取平仓信号: {message[:100]}...")
    
    # 检查是否包含平仓关键词
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    has_close_signal = any(keyword in message for keyword in close_keywords)
    
    if not has_close_signal:
        # 如果没有标准平仓关键词，检查通用平仓信号
        close_patterns = [
            r'平仓\s*([A-Z]+)',  # 平仓 ETH
            r'([A-Z]+)\s*平仓',  # ETH 平仓
            r'平多\s*([A-Z]+)',  # 平多 ETH
            r'([A-Z]+)\s*平多',  # ETH 平多
            r'平空\s*([A-Z]+)',  # 平空 ETH
            r'([A-Z]+)\s*平空',  # ETH 平空
            r'CLOSE\s*([A-Z]+)',  # CLOSE ETH
            r'([A-Z]+)\s*CLOSE'  # ETH CLOSE
        ]
        
        for pattern in close_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                symbol = match.group(1)
                print(f"检测到通用平仓信号: {symbol}")
                return 'both', symbol
        
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
test_messages = [
    # 标准格式的开仓信号
    "策略当前交易对:ETHUSDT.P\n==========================\nETH价格:2435.10\n===========================\n执行交易:做空 0.072ETH\n===========================",
    
    # 标准格式的平仓信号
    "策略当前交易对:ETHUSDT.P\n==========================\nETH价格:2435.10\n===========================\n空止盈:做空 0.072ETH\n===========================",
    
    # 通用格式的开仓信号
    "做多 ETH",
    "做空 0.072ETH",
    "买入 BTC",
    "LONG ETH",
    "SHORT BTC",
    
    # 通用格式的平仓信号
    "平仓 ETH",
    "平多 BTC",
    "平空 ETH",
    "CLOSE BTC"
]

print("=== 新的交易信号提取函数测试 ===")
for i, message in enumerate(test_messages, 1):
    print(f"\n--- 测试消息 {i} ---")
    print(f"消息: {message}")
    
    # 测试开仓信号提取
    action, symbol = extract_trade_info(message)
    if action and symbol:
        print(f"开仓信号: {action} {symbol}")
    else:
        print("开仓信号: 未检测到")
    
    # 测试平仓信号提取
    close_type, close_symbol = extract_close_signal(message)
    if close_type and close_symbol:
        print(f"平仓信号: {close_type} {close_symbol}")
    else:
        print("平仓信号: 未检测到")
    
    print("-" * 50) 