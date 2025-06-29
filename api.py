from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import json

from models import create_tables
from database import DatabaseManager, FileManager

# 创建FastAPI应用
app = FastAPI(title="Telegram Trading Bot API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
create_tables()

# 初始化文件管理器
file_manager = FileManager()

# 数据模型
class TradingOrderResponse(BaseModel):
    id: int
    timestamp: str
    account_name: str
    action: str
    symbol: str
    quantity: float
    price: float
    market_price: float
    order_id: str
    status: str
    error_message: Optional[str] = None
    profit_loss: Optional[float] = None
    close_time: Optional[str] = None

class TelegramMessageResponse(BaseModel):
    id: int
    timestamp: str
    group_id: str
    group_title: str
    sender_name: str
    message_text: str
    has_signal: bool
    signal_type: Optional[str] = None
    signal_action: Optional[str] = None
    signal_symbol: Optional[str] = None

class TradingStatisticsResponse(BaseModel):
    total_orders: int
    successful_orders: int
    failed_orders: int
    success_rate: float
    total_profit_loss: float
    period: Dict[str, Optional[str]]

# API路由

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Telegram Trading Bot API", "version": "1.0.0"}

@app.get("/api/orders", response_model=List[TradingOrderResponse])
async def get_orders(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    account_name: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取交易订单列表"""
    try:
        with DatabaseManager() as db:
            # 解析日期
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            orders = db.get_trading_orders(
                limit=limit,
                offset=offset,
                account_name=account_name,
                symbol=symbol,
                start_date=start_dt,
                end_date=end_dt
            )
            return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单失败: {str(e)}")

@app.get("/api/messages", response_model=List[TelegramMessageResponse])
async def get_messages(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    group_id: Optional[str] = Query(None),
    has_signal: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取Telegram消息列表"""
    try:
        with DatabaseManager() as db:
            # 解析日期
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            messages = db.get_telegram_messages(
                limit=limit,
                offset=offset,
                group_id=group_id,
                has_signal=has_signal,
                start_date=start_dt,
                end_date=end_dt
            )
            return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")

@app.get("/api/statistics", response_model=TradingStatisticsResponse)
async def get_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取交易统计"""
    try:
        with DatabaseManager() as db:
            # 解析日期
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            stats = db.get_trading_statistics(start_date=start_dt, end_date=end_dt)
            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@app.get("/api/logs")
async def get_logs(
    date: Optional[str] = Query(None, description="日志日期，格式：YYYY-MM-DD"),
    lines: int = Query(100, ge=1, le=1000)
):
    """获取系统日志"""
    try:
        log_lines = file_manager.read_log_file(date=date, lines=lines)
        return {
            "date": date or datetime.now().strftime('%Y-%m-%d'),
            "lines": lines,
            "log_content": log_lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

@app.get("/api/logs/dates")
async def get_available_log_dates():
    """获取可用的日志日期列表"""
    try:
        dates = file_manager.get_available_log_dates()
        return {"available_dates": dates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志日期失败: {str(e)}")

@app.get("/api/orders/summary")
async def get_orders_summary(
    days: int = Query(7, ge=1, le=365, description="统计天数")
):
    """获取订单摘要统计"""
    try:
        with DatabaseManager() as db:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 按日期分组统计
            orders = db.get_trading_orders(
                limit=10000,  # 获取足够多的数据
                start_date=start_date,
                end_date=end_date
            )
            
            # 按日期分组
            daily_stats = {}
            for order in orders:
                order_date = order['timestamp'][:10]  # 提取日期部分
                if order_date not in daily_stats:
                    daily_stats[order_date] = {
                        'total_orders': 0,
                        'successful_orders': 0,
                        'failed_orders': 0,
                        'total_profit_loss': 0.0
                    }
                
                daily_stats[order_date]['total_orders'] += 1
                if order['status'] == '成功':
                    daily_stats[order_date]['successful_orders'] += 1
                else:
                    daily_stats[order_date]['failed_orders'] += 1
                
                if order['profit_loss']:
                    daily_stats[order_date]['total_profit_loss'] += order['profit_loss']
            
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "daily_statistics": daily_stats
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单摘要失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    try:
        with DatabaseManager() as db:
            # 简单测试数据库连接
            db.get_trading_orders(limit=1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "file_manager": "ready"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    print("Telegram Trading Bot API 启动中...")
    print(f"数据存储路径: {file_manager.base_path}")
    print("API服务已就绪")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("Telegram Trading Bot API 正在关闭...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 