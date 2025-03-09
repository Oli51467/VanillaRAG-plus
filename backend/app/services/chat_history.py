from typing import List, Optional
from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain.memory.chat_message_histories.sql import SQLChatMessageHistory
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
import uuid

from app.db.models import Conversation, ConversationMessage
from app.db.database import SessionLocal

class PostgresChatMessageHistory(SQLChatMessageHistory):
    """PostgreSQL实现的聊天消息历史"""
    
    def __init__(self, conversation_id: str, session: Optional[Session] = None):
        """
        初始化PostgreSQL聊天消息历史
        
        Args:
            conversation_id: 对话ID
            session: SQLAlchemy会话，如果不提供则创建新的
        """
        self.conversation_id = conversation_id
        self._session = session or SessionLocal()
        self._is_external_session = session is not None
    
    def add_message(self, message: BaseMessage) -> None:
        """
        添加消息到历史记录
        
        Args:
            message: LangChain消息对象
        """
        # 获取当前最大序列号
        stmt = select(func.max(ConversationMessage.sequence)).where(
            ConversationMessage.conversation_id == self.conversation_id
        )
        result = self._session.execute(stmt).scalar()
        next_sequence = (result or 0) + 1
        
        # 创建新消息
        message_entry = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=self.conversation_id,
            role=message.type,
            content=message.content,
            sequence=next_sequence
        )
        
        self._session.add(message_entry)
        self._session.commit()
    
    def add_user_message(self, message: str) -> None:
        """添加用户消息"""
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """添加AI消息"""
        self.add_message(AIMessage(content=message))
    
    def add_system_message(self, message: str) -> None:
        """添加系统消息"""
        self.add_message(SystemMessage(content=message))
    
    def clear(self) -> None:
        """清空对话历史"""
        stmt = delete(ConversationMessage).where(
            ConversationMessage.conversation_id == self.conversation_id
        )
        self._session.execute(stmt)
        self._session.commit()
    
    def messages(self) -> List[BaseMessage]:
        """
        获取所有消息
        
        Returns:
            消息列表
        """
        stmt = select(ConversationMessage).where(
            ConversationMessage.conversation_id == self.conversation_id
        ).order_by(ConversationMessage.sequence)
        
        result = self._session.execute(stmt).scalars().all()
        
        messages = []
        for message_entry in result:
            if message_entry.role == "human":
                messages.append(HumanMessage(content=message_entry.content))
            elif message_entry.role == "ai":
                messages.append(AIMessage(content=message_entry.content))
            elif message_entry.role == "system":
                messages.append(SystemMessage(content=message_entry.content))
        
        return messages
    
    def __del__(self):
        """析构函数，关闭会话"""
        if not self._is_external_session and self._session:
            self._session.close() 