from sqlalchemy.orm import Session
from models import TradingOrder, TelegramMessage, SystemLog, BotSession, SessionLocal
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import json

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def close(self):
        self.db.close()
    
    # 交易订单相关方法
    def add_trading_order(self, order_data: Dict) -> TradingOrder:
        """添加交易订单"""
        order = TradingOrder(**order_data)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def get_trading_orders(self, limit: int = 100, offset: int = 0, 
                          account_name: Optional[str] = None,
                          symbol: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict]:
        """获取交易订单"""
        query = self.db.query(TradingOrder)
        
        if account_name:
            query = query.filter(TradingOrder.account_name == account_name)
        if symbol:
            query = query.filter(TradingOrder.symbol == symbol)
        if start_date:
            query = query.filter(TradingOrder.timestamp >= start_date)
        if end_date:
            query = query.filter(TradingOrder.timestamp <= end_date)
        
        orders = query.order_by(TradingOrder.timestamp.desc()).offset(offset).limit(limit).all()
        return [order.to_dict() for order in orders]
    
    def update_order_profit_loss(self, order_id: int, profit_loss: float, close_time: datetime = None):
        """更新订单盈亏"""
        order = self.db.query(TradingOrder).filter(TradingOrder.id == order_id).first()
        if order:
            order.profit_loss = profit_loss
            if close_time:
                order.close_time = close_time
            self.db.commit()
    
    # Telegram消息相关方法
    def add_telegram_message(self, message_data: Dict) -> TelegramMessage:
        """添加Telegram消息"""
        message = TelegramMessage(**message_data)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_telegram_messages(self, limit: int = 100, offset: int = 0,
                             group_id: Optional[str] = None,
                             has_signal: Optional[bool] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict]:
        """获取Telegram消息"""
        query = self.db.query(TelegramMessage)
        
        if group_id:
            query = query.filter(TelegramMessage.group_id == group_id)
        if has_signal is not None:
            query = query.filter(TelegramMessage.has_signal == has_signal)
        if start_date:
            query = query.filter(TelegramMessage.timestamp >= start_date)
        if end_date:
            query = query.filter(TelegramMessage.timestamp <= end_date)
        
        messages = query.order_by(TelegramMessage.timestamp.desc()).offset(offset).limit(limit).all()
        return [message.to_dict() for message in messages]
    
    # 系统日志相关方法
    def add_system_log(self, level: str, module: str, message: str) -> SystemLog:
        """添加系统日志"""
        log = SystemLog(level=level, module=module, message=message)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_system_logs(self, limit: int = 100, offset: int = 0,
                       level: Optional[str] = None,
                       module: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict]:
        """获取系统日志"""
        query = self.db.query(SystemLog)
        
        if level:
            query = query.filter(SystemLog.level == level)
        if module:
            query = query.filter(SystemLog.module == module)
        if start_date:
            query = query.filter(SystemLog.timestamp >= start_date)
        if end_date:
            query = query.filter(SystemLog.timestamp <= end_date)
        
        logs = query.order_by(SystemLog.timestamp.desc()).offset(offset).limit(limit).all()
        return [log.to_dict() for log in logs]
    
    # 机器人会话相关方法
    def get_or_create_bot_session(self, session_name: str, phone_number: str) -> BotSession:
        """获取或创建机器人会话"""
        session = self.db.query(BotSession).filter(BotSession.session_name == session_name).first()
        if not session:
            session = BotSession(session_name=session_name, phone_number=phone_number)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def update_session_authorization(self, session_name: str, is_authorized: bool):
        """更新会话授权状态"""
        session = self.db.query(BotSession).filter(BotSession.session_name == session_name).first()
        if session:
            session.is_authorized = is_authorized
            session.last_login = datetime.utcnow()
            self.db.commit()
    
    def get_bot_session(self, session_name: str) -> Optional[Dict]:
        """获取机器人会话"""
        session = self.db.query(BotSession).filter(BotSession.session_name == session_name).first()
        return session.to_dict() if session else None
    
    # 统计方法
    def get_trading_statistics(self, start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None) -> Dict:
        """获取交易统计"""
        query = self.db.query(TradingOrder)
        
        if start_date:
            query = query.filter(TradingOrder.timestamp >= start_date)
        if end_date:
            query = query.filter(TradingOrder.timestamp <= end_date)
        
        total_orders = query.count()
        successful_orders = query.filter(TradingOrder.status == '成功').count()
        failed_orders = query.filter(TradingOrder.status == '失败').count()
        
        # 计算总盈亏
        profit_orders = query.filter(TradingOrder.profit_loss.isnot(None)).all()
        total_profit_loss = sum(order.profit_loss for order in profit_orders if order.profit_loss)
        
        return {
            'total_orders': total_orders,
            'successful_orders': successful_orders,
            'failed_orders': failed_orders,
            'success_rate': (successful_orders / total_orders * 100) if total_orders > 0 else 0,
            'total_profit_loss': total_profit_loss,
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }

class FileManager:
    """文件管理器 - 管理Session文件和日志文件"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getenv('DATA_PATH', './data')
        self.session_path = os.path.join(self.base_path, 'sessions')
        self.logs_path = os.path.join(self.base_path, 'logs')
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保目录存在"""
        os.makedirs(self.session_path, exist_ok=True)
        os.makedirs(self.logs_path, exist_ok=True)
    
    def get_session_file_path(self, session_name: str) -> str:
        """获取Session文件路径"""
        return os.path.join(self.session_path, f"{session_name}.session")
    
    def session_exists(self, session_name: str) -> bool:
        """检查Session文件是否存在"""
        return os.path.exists(self.get_session_file_path(session_name))
    
    def get_log_file_path(self, date: str = None) -> str:
        """获取日志文件路径"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.logs_path, f"tg_bot_{date}.log")
    
    def get_order_log_path(self) -> str:
        """获取订单日志文件路径"""
        return os.path.join(self.logs_path, 'ordered_list.log')
    
    def read_log_file(self, date: str = None, lines: int = 100) -> List[str]:
        """读取日志文件"""
        log_path = self.get_log_file_path(date)
        if not os.path.exists(log_path):
            return []
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines_list = f.readlines()
                return lines_list[-lines:] if len(lines_list) > lines else lines_list
        except Exception as e:
            print(f"读取日志文件失败: {e}")
            return []
    
    def write_order_log(self, order_info: Dict):
        """写入订单日志"""
        log_path = self.get_order_log_path()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 自动将所有datetime字段转为字符串
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            else:
                return obj
        safe_order_info = convert(order_info)
        order_record = f"{timestamp} | {json.dumps(safe_order_info, ensure_ascii=False)}"
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(order_record + '\n')
        except Exception as e:
            print(f"写入订单日志失败: {e}")
    
    def get_available_log_dates(self) -> List[str]:
        """获取可用的日志日期列表"""
        dates = []
        for filename in os.listdir(self.logs_path):
            if filename.startswith('tg_bot_') and filename.endswith('.log'):
                date = filename[7:-4]  # 提取日期部分
                dates.append(date)
        return sorted(dates, reverse=True) 