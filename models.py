from sqlalchemy import Column, Integer, String, Boolean, Text
from database import Base

class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(String)
    api_hash = Column(String)
    phone_number = Column(String)
    bark_api_key = Column(String)
    log_group_id = Column(String)
    is_running = Column(Boolean, default=False)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String, unique=True)

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text) 