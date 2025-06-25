# bot/core/__init__.py
"""
交易机器人核心模块

此包包含交易机器人的核心功能：
- 配置管理
- 数据库操作
- 日志记录
- 状态监控
- 认证功能
"""

# 导出核心功能
from .config import get_config, update_config
from .db import (
    update_status, get_status,
    log_message, get_logs,
    get_user, verify_password
)
from .bot import TradingBot