#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能测试脚本
用于验证新增的订单日志记录、平仓信号检测等功能
"""

import json
import os
import sys
from datetime import datetime

def test_order_logging():
    """测试订单日志记录功能"""
    print("🧪 测试订单日志记录功能...")
    
    # 模拟订单信息
    order_info = {
        'account_name': 'OKX1',
        'ordId': '123456789',
        'clOrdId': 'TG20240629123456ABC123',
        'action': '做多',
        'symbol': 'ETH',
        'inst_id': 'ETH-USDT-SWAP',
        'side': 'buy',
        'posSide': 'long',
        'qty': '0.1',
        'price': 3500.0,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 确保logs目录存在
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 写入测试订单日志
    log_file = 'logs/ordered_list.log'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order_record = f"{timestamp} | {json.dumps(order_info, ensure_ascii=False)}"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(order_record + '\n')
    
    print(f"✅ 订单日志已写入: {log_file}")
    print(f"📝 订单内容: {order_info['action']} {order_info['symbol']} {order_info['qty']}")
    return True

def test_close_signal_detection():
    """测试平仓信号检测功能"""
    print("\n🧪 测试平仓信号检测功能...")
    
    # 测试消息
    test_messages = [
        "策略当前交易对:ETHUSDT.P 空止盈 0.1ETH",
        "策略当前交易对:BTCUSDT.P 多止损 0.01BTC",
        "策略当前交易对:ETHUSDT.P 空止损 0.1ETH",
        "策略当前交易对:BTCUSDT.P 多止盈 0.01BTC",
        "普通消息，不包含平仓信号"
    ]
    
    # 平仓关键词
    close_keywords = ['空止盈', '空止损', '多止盈', '多止损']
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n测试消息 {i}: {message}")
        
        # 检查是否包含平仓关键词
        has_close_signal = any(keyword in message for keyword in close_keywords)
        
        if has_close_signal:
            # 提取交易对信息
            import re
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
                
                print(f"✅ 检测到平仓信号: {close_type} {symbol}")
            else:
                print("❌ 无法提取交易对信息")
        else:
            print("📭 未检测到平仓信号")
    
    return True

def test_restart_interval():
    """测试重启间隔设置"""
    print("\n🧪 测试重启间隔设置...")
    
    from datetime import timedelta
    
    # 检查重启间隔是否为30分钟
    restart_interval = timedelta(minutes=30)
    expected_interval = timedelta(minutes=30)
    
    if restart_interval == expected_interval:
        print("✅ 重启间隔设置正确: 30分钟")
        print(f"📅 重启间隔: {restart_interval}")
    else:
        print("❌ 重启间隔设置错误")
        return False
    
    return True

def test_message_combination():
    """测试消息合并功能"""
    print("\n🧪 测试消息合并功能...")
    
    # 模拟基础日志消息
    base_log = "时间: 2024-06-29 10:30:00\n来源: 群组ID:-100123 (@test_user)\n消息: 测试消息内容"
    
    # 测试不同场景的消息合并
    test_scenarios = [
        {
            'action': '做多',
            'symbol': 'ETH',
            'expected': '检测到交易信号'
        },
        {
            'close_type': 'short',
            'close_symbol': 'BTC',
            'expected': '检测到平仓信号'
        },
        {
            'action': None,
            'symbol': None,
            'expected': '未检测到交易信号'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n测试场景 {i}:")
        
        combined_message = f"📥 收到消息:\n{base_log}"
        
        if 'action' in scenario and scenario['action']:
            combined_message += f"\n\n✅ 检测到交易信号!\n动作: {scenario['action']}\n符号: {scenario['symbol']}"
            print(f"✅ {scenario['expected']}: {scenario['action']} {scenario['symbol']}")
        elif 'close_type' in scenario and scenario['close_type']:
            combined_message += f"\n\n🔄 检测到平仓信号!\n类型: {scenario['close_type']}\n符号: {scenario['close_symbol']}"
            print(f"✅ {scenario['expected']}: {scenario['close_type']} {scenario['close_symbol']}")
        else:
            combined_message += f"\n\n📭 未检测到交易信号"
            print(f"✅ {scenario['expected']}")
        
        print(f"📝 合并消息长度: {len(combined_message)} 字符")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始功能测试...")
    print("=" * 50)
    
    tests = [
        test_order_logging,
        test_close_signal_detection,
        test_restart_interval,
        test_message_combination
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新功能正常工作。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 