import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'db' / 'config.db'


def create_config_db():
    """创建配置数据库"""
    os.makedirs(DB_PATH.parent, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 创建基础配置表
    c.execute('''CREATE TABLE IF NOT EXISTS configs
                 (id INTEGER PRIMARY KEY,
                  name TEXT UNIQUE,
                  content TEXT,
                  last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 创建默认配置
    default_configs = {
        'telegram_config': {
            'api_id': '',
            'api_hash': '',
            'phone_number': '',
            'bark_api_key': '',
            'log_group_id': '',
            'proxy': {'protocol': 'socks5', 'host': '127.0.0.1', 'port': 12334}
        },
        'okx_config': {
            'accounts': [
                {
                    'account_name': 'Account1-PROD',
                    'API_KEY': '',
                    'SECRET_KEY': '',
                    'PASSPHRASE': '',
                    'FLAG': '1',
                    'LEVERAGE': 10,
                    'FIXED_QTY': {'ETH': 1, 'BTC': 1}
                },
                {
                    'account_name': 'Account2-QA',
                    'API_KEY': '',
                    'SECRET_KEY': '',
                    'PASSPHRASE': '',
                    'FLAG': '0',
                    'LEVERAGE': 10,
                    'FIXED_QTY': {'ETH': 1, 'BTC': 1}
                }
            ]
        },
        'listen_groups': [-1001638841860, -4831222036]
    }

    # 插入或更新配置
    for name, content in default_configs.items():
        c.execute('''INSERT OR REPLACE INTO configs (name, content, last_modified)
                     VALUES (?, ?, ?)''',
                  (name, json.dumps(content), datetime.now()))

    conn.commit()
    conn.close()


def get_config(name):
    """获取配置"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT content FROM configs WHERE name = ?', (name,))
    result = c.fetchone()
    conn.close()

    return json.loads(result[0]) if result else None


def update_config(name, content):
    """更新配置"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''UPDATE configs 
                 SET content = ?, last_modified = ?
                 WHERE name = ?''',
              (json.dumps(content), datetime.now(), name))
    conn.commit()
    conn.close()


# 第一次运行时创建数据库
if not DB_PATH.exists():
    create_config_db()