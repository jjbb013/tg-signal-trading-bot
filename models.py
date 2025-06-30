from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 创建数据库引擎
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/trading_bot.db')

# 确保数据库目录存在
if DATABASE_URL.startswith('sqlite:///'):
    db_path = DATABASE_URL.replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

class TradingOrder(Base):
    """交易订单表"""
    __tablename__ = "trading_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    account_name = Column(String(100), index=True)
    action = Column(String(50))  # 做多、做空、平仓
    symbol = Column(String(20))  # ETH、BTC等
    quantity = Column(Float)
    price = Column(Float)
    market_price = Column(Float)
    order_id = Column(String(100))
    status = Column(String(50))  # 成功、失败
    error_message = Column(Text, nullable=True)
    profit_loss = Column(Float, nullable=True)  # 盈亏
    close_time = Column(DateTime, nullable=True)  # 平仓时间
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'account_name': self.account_name,
            'action': self.action,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'market_price': self.market_price,
            'order_id': self.order_id,
            'status': self.status,
            'error_message': self.error_message,
            'profit_loss': self.profit_loss,
            'close_time': self.close_time.isoformat() if self.close_time else None
        }

class TelegramMessage(Base):
    """Telegram消息记录表"""
    __tablename__ = "telegram_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    group_id = Column(String(100), index=True)
    group_title = Column(String(200))
    sender_name = Column(String(200))
    message_text = Column(Text)
    has_signal = Column(Boolean, default=False)
    signal_type = Column(String(50), nullable=True)  # 交易信号、平仓信号
    signal_action = Column(String(50), nullable=True)
    signal_symbol = Column(String(20), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'group_id': self.group_id,
            'group_title': self.group_title,
            'sender_name': self.sender_name,
            'message_text': self.message_text,
            'has_signal': self.has_signal,
            'signal_type': self.signal_type,
            'signal_action': self.signal_action,
            'signal_symbol': self.signal_symbol
        }

class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20))  # INFO, WARNING, ERROR, DEBUG
    module = Column(String(100))
    message = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'module': self.module,
            'message': self.message
        }

class BotSession(Base):
    """机器人会话状态表"""
    __tablename__ = "bot_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(100), unique=True, index=True)
    phone_number = Column(String(20))
    is_authorized = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_name': self.session_name,
            'phone_number': self.phone_number,
            'is_authorized': self.is_authorized,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 创建所有表
def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 