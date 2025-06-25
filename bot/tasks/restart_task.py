# bot/tasks/restart_task.py
import asyncio
import logging
from datetime import datetime, timedelta
from core.bot import TradingBot

logger = logging.getLogger('tg_bot')


async def schedule_restart(bot: TradingBot, interval_hours: int = 2):
    """
    定时重启任务

    :param bot: 交易机器人实例
    :param interval_hours: 重启间隔小时数
    """
    while bot.running:
        # 计算下一次重启时间
        next_restart = datetime.now() + timedelta(hours=interval_hours)
        logger.info(f"计划在 {next_restart} 重启机器人")

        # 等待直到重启时间
        while datetime.now() < next_restart and bot.running:
            await asyncio.sleep(60)  # 每分钟检查一次

        if not bot.running:
            break

        logger.info("执行定时重启...")
        await bot.restart()