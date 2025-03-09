from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, engine
from app.db.models import Conversation, ConversationMessage

def init_db():
    """初始化数据库表"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")

if __name__ == "__main__":
    init_db() 