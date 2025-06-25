import os
import sqlite3
import logging
from datetime import datetime
import hashlib
from pathlib import Path

logger = logging.getLogger('tg_bot')

# 数据库路径
DB_PATH = Path(__file__).parent / 'db' / 'bot.db'


def create_bot_db():
    """创建机器人状态数据库"""
    os.makedirs(DB_PATH.parent, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 创建状态表
    c.execute('''CREATE TABLE IF NOT EXISTS status
                 (id INTEGER PRIMARY KEY,
                  name TEXT UNIQUE,
                  value TEXT,
                  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 创建日志表
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  level TEXT,
                  message TEXT)''')

    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # 初始状态
    c.execute('''INSERT OR IGNORE INTO status (name, value) 
                 VALUES ('bot_status', 'stopped')''')

    c.execute('''INSERT OR IGNORE INTO status (name, value) 
                 VALUES ('restart_count', '0')''')

    c.execute('''INSERT OR IGNORE INTO status (name, value) 
                 VALUES ('last_restart', ?)''', (datetime.now().isoformat(),))

    # 创建管理员用户
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    if admin_password:
        try:
            # 尝试使用 Werkzeug 生成密码哈希
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(admin_password)
        except ImportError:
            # 如果 Werkzeug 不可用，使用 SHA256 作为备用
            logger.warning("Werkzeug not installed, using SHA256 for password hashing")
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()

        c.execute('''INSERT OR IGNORE INTO users (username, password_hash)
                     VALUES (?, ?)''', ('admin', password_hash))

    conn.commit()
    conn.close()


def update_status(name, value):
    """更新状态"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO status (name, value, last_updated)
                 VALUES (?, ?, ?)''',
              (name, str(value), datetime.now()))
    conn.commit()
    conn.close()


def get_status(name):
    """获取状态"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM status WHERE name = ?', (name,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def log_message(level, message):
    """记录日志"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO logs (level, message)
                 VALUES (?, ?)''',
              (level, message))
    conn.commit()
    conn.close()


def get_logs(limit=100):
    """获取日志"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT timestamp, level, message 
                 FROM logs 
                 ORDER BY timestamp DESC 
                 LIMIT ?''', (limit,))
    logs = [{'timestamp': row[0], 'level': row[1], 'message': row[2]}
            for row in c.fetchall()]
    conn.close()
    return logs


def get_user(username):
    """获取用户信息"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()

    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password_hash': user[2],
            'created_at': user[3]
        }
    return None


def verify_password(username, password):
    """验证用户名和密码"""
    user = get_user(username)
    if not user:
        return False

    try:
        # 尝试使用 Werkzeug 验证密码
        from werkzeug.security import check_password_hash
        return check_password_hash(user['password_hash'], password)
    except ImportError:
        # 如果 Werkzeug 不可用，使用 SHA256 作为备用
        return user['password_hash'] == hashlib.sha256(password.encode()).hexdigest()


# 第一次运行时创建数据库
if not DB_PATH.exists():
    create_bot_db()