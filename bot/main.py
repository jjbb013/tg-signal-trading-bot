import asyncio
import logging
import traceback  # 添加 traceback 模块导入
from core.bot import TradingBot


# 设置日志
def setup_logger():
    """设置日志记录器"""
    logger = logging.getLogger('tg_bot')
    logger.setLevel(logging.DEBUG)

    # 创建文件处理器
    file_handler = logging.FileHandler('tg_bot.log')
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


async def main():
    """主函数"""
    logger = setup_logger()

    try:
        logger.info("=" * 50)
        logger.info("启动交易机器人系统")
        logger.info("=" * 50)

        # 创建交易机器人实例
        bot = TradingBot()

        # 初始化机器人
        await bot.initialize()

        # 启动机器人
        await bot.start()

        # 保持运行直到被中断
        while bot.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("用户中断程序，退出...")
    except Exception as e:
        logger.error(f"主程序运行出错: {e}")
        logger.error(traceback.format_exc())  # 现在可以正常使用 traceback
    finally:
        # 确保机器人正确停止
        if bot.running:
            await bot.stop()

        logger.info("=" * 50)
        logger.info("交易机器人系统已停止")
        logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())