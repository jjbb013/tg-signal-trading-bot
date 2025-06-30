#!/usr/bin/env python3
"""
数据库初始化脚本
用于在容器启动时确保数据库目录和文件正确创建
"""

import os
import sys
from pathlib import Path

def init_database():
    """初始化数据库目录和文件"""
    try:
        # 获取数据库路径
        data_path = os.getenv('DATA_PATH', '/data')
        db_path = os.path.join(data_path, 'trading_bot.db')
        
        # 确保数据目录存在
        os.makedirs(data_path, exist_ok=True)
        os.makedirs(os.path.join(data_path, 'sessions'), exist_ok=True)
        os.makedirs(os.path.join(data_path, 'logs'), exist_ok=True)
        
        # 设置权限
        os.chmod(data_path, 0o755)
        os.chmod(os.path.join(data_path, 'sessions'), 0o755)
        os.chmod(os.path.join(data_path, 'logs'), 0o755)
        
        # 设置数据库环境变量
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        
        print(f"数据库目录初始化完成: {data_path}")
        print(f"数据库文件路径: {db_path}")
        
        # 尝试创建数据库表
        try:
            from models import create_tables
            create_tables()
            print("数据库表创建成功")
        except Exception as e:
            print(f"数据库表创建失败: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1) 