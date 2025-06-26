from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Config, Group, Log
from bot import BotManager
from fastapi.staticfiles import StaticFiles
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

import threading
import json
import os
import asyncio
from datetime import datetime

Base.metadata.create_all(bind=engine)

# 自动导入 telegram_config.json 到数据库
if os.path.exists("telegram_config.json"):
    with open("telegram_config.json", "r") as f:
        config_json = json.load(f)
    db = SessionLocal()
    config = db.query(Config).first()
    if not config:
        config = Config()
        db.add(config)
    config.api_id = config_json.get("api_id")
    config.api_hash = config_json.get("api_hash")
    config.phone_number = config_json.get("phone_number")
    config.bark_api_key = config_json.get("bark_api_key")
    config.log_group_id = str(config_json.get("log_group_id"))
    proxy = config_json.get("proxy", {})
    config.proxy_protocol = proxy.get("protocol")
    config.proxy_host = proxy.get("host")
    config.proxy_port = proxy.get("port")
    db.commit()
    db.close()

# 自动导入 listen_group.txt 到数据库
if os.path.exists("listen_group.txt"):
    db = SessionLocal()
    with open("listen_group.txt", "r", encoding="utf-8") as f:
        for line in f:
            if 'ID:' in line:
                group_id = line.split('ID: ')[1].strip()
                # 检查是否已存在
                if not db.query(Group).filter_by(group_id=group_id).first():
                    db.add(Group(group_id=group_id))
    db.commit()
    db.close()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

bot_manager = None
bot_thread = None

login_state = {"step": "idle", "error": "", "phone": ""}
login_tmp = {"phone": None, "client": None}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_callback(content):
    db = SessionLocal()
    db.add(Log(content=content))
    db.commit()
    db.close()
    # 写入 logs 目录下的日志文件
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, datetime.now().strftime('%Y-%m-%d') + '.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(content + '\n')

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    db = next(get_db())
    config = db.query(Config).first()
    groups = db.query(Group).all()
    logs = db.query(Log).order_by(Log.id.desc()).limit(50).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "config": config,
        "groups": groups,
        "logs": logs,
    })

@app.post("/config")
def update_config(
    api_id: str = Form(...),
    api_hash: str = Form(...),
    phone_number: str = Form(...),
    bark_api_key: str = Form(...),
    log_group_id: str = Form(...),
    proxy_protocol: str = Form(None),
    proxy_host: str = Form(None),
    proxy_port: int = Form(None)
):
    db = next(get_db())
    config = db.query(Config).first()
    if not config:
        config = Config()
        db.add(config)
    config.api_id = api_id
    config.api_hash = api_hash
    config.phone_number = phone_number
    config.bark_api_key = bark_api_key
    config.log_group_id = log_group_id
    config.proxy_protocol = proxy_protocol
    config.proxy_host = proxy_host
    config.proxy_port = proxy_port
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/group/add")
def add_group(group_id: str = Form(...)):
    db = next(get_db())
    if not db.query(Group).filter_by(group_id=group_id).first():
        db.add(Group(group_id=group_id))
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/group/delete")
def delete_group(group_id: str = Form(...)):
    db = next(get_db())
    group = db.query(Group).filter_by(group_id=group_id).first()
    if group:
        db.delete(group)
        db.commit()
    return RedirectResponse("/", status_code=303)

async def get_config():
    db = next(get_db())
    config = db.query(Config).first()
    return config

@app.post("/tg_login/start")
async def tg_login_start(phone: str = Form(...)):
    global login_state, login_tmp
    config = await get_config()
    if not config:
        return JSONResponse({"ok": False, "error": "请先配置参数"})
    login_state = {"step": "code", "error": "", "phone": phone}
    try:
        client = TelegramClient(f'session_{phone}', config.api_id, config.api_hash)
        await client.connect()
        await client.send_code_request(phone)
        login_tmp = {"phone": phone, "client": client}
        return JSONResponse({"ok": True, "step": "code"})
    except Exception as e:
        login_state = {"step": "idle", "error": str(e), "phone": phone}
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/tg_login/code")
async def tg_login_code(code: str = Form(...)):
    global login_state, login_tmp
    phone = login_state.get("phone")
    client = login_tmp.get("client")
    try:
        await client.sign_in(phone, code)
        if await client.is_user_authorized():
            login_state = {"step": "done", "error": "", "phone": phone}
            await client.disconnect()
            return JSONResponse({"ok": True, "step": "done"})
        else:
            login_state = {"step": "password", "error": "", "phone": phone}
            return JSONResponse({"ok": True, "step": "password"})
    except SessionPasswordNeededError:
        login_state = {"step": "password", "error": "", "phone": phone}
        return JSONResponse({"ok": True, "step": "password"})
    except PhoneCodeInvalidError:
        login_state = {"step": "code", "error": "验证码错误，请重试", "phone": phone}
        return JSONResponse({"ok": False, "error": "验证码错误，请重试"})
    except Exception as e:
        login_state = {"step": "idle", "error": str(e), "phone": phone}
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/tg_login/password")
async def tg_login_password(password: str = Form(...)):
    global login_state, login_tmp
    phone = login_state.get("phone")
    client = login_tmp.get("client")
    try:
        await client.sign_in(password=password)
        if await client.is_user_authorized():
            login_state = {"step": "done", "error": "", "phone": phone}
            await client.disconnect()
            return JSONResponse({"ok": True, "step": "done"})
        else:
            login_state = {"step": "idle", "error": "登录失败", "phone": phone}
            return JSONResponse({"ok": False, "error": "登录失败"})
    except Exception as e:
        login_state = {"step": "idle", "error": str(e), "phone": phone}
        return JSONResponse({"ok": False, "error": str(e)})

@app.get("/tg_login/status")
async def tg_login_status():
    global login_state
    return JSONResponse(login_state)

# 启动监听前检测 session
@app.post("/bot/start")
async def start_bot():
    global bot_manager, bot_thread
    db = next(get_db())
    config = db.query(Config).first()
    groups = db.query(Group).all()
    if not config or not groups:
        return RedirectResponse("/", status_code=303)
    # 检查 session 是否已登录
    try:
        async with TelegramClient(f'session_{config.phone_number}', config.api_id, config.api_hash) as client:
            if not await client.is_user_authorized():
                return JSONResponse({"ok": False, "need_login": True, "msg": "未登录，请先登录 Telegram"})
    except Exception as e:
        return JSONResponse({"ok": False, "need_login": True, "msg": f"登录检测失败: {e}"})
    if bot_manager and bot_manager.running:
        return RedirectResponse("/", status_code=303)
    bot_manager = BotManager(config, groups, log_callback)
    bot_thread = threading.Thread(target=bot_manager.start)
    bot_thread.start()
    config.is_running = True
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/bot/stop")
def stop_bot():
    global bot_manager
    db = next(get_db())
    if bot_manager:
        bot_manager.stop()
    config = db.query(Config).first()
    if config:
        config.is_running = False
        db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/logs")
def get_logs():
    db = next(get_db())
    logs = db.query(Log).order_by(Log.id.desc()).limit(50).all()
    # 倒序显示最新在下方
    logs = [log.content for log in reversed(logs)]
    return JSONResponse(content={"logs": logs})

@app.get("/logs/list")
def list_log_files():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        return JSONResponse({"files": []})
    files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
    return JSONResponse({"files": files})

@app.get("/logs/file")
def get_log_file(date: str):
    log_dir = 'logs'
    log_file = os.path.join(log_dir, f'{date}.log')
    if not os.path.exists(log_file):
        return JSONResponse({"content": "日志文件不存在"})
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    return JSONResponse({"content": content}) 