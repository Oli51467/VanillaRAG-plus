from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, func
import uuid
from datetime import datetime

from db.models import Conversation, ConversationMessage
from service.chat_history import PostgresChatMessageHistory

class ConversationService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, title: str, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            title=title,
            meta_data=metadata or {}
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result
    
    def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Conversation]:
        stmt = select(Conversation).order_by(desc(Conversation.created_at)).limit(limit).offset(offset)
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def delete_conversation(self, conversation_id: str) -> bool:
        # 先删除消息
        msg_stmt = delete(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id)
        self.db.execute(msg_stmt)
        
        # 再删除对话
        conv_stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = self.db.execute(conv_stmt)
        
        self.db.commit()
        
        return result.rowcount > 0
    
    def add_message(self, conversation_id: str, role: str, content: str) -> ConversationMessage:
        # 获取当前最大序列号
        stmt = select(func.max(ConversationMessage.sequence)).where(
            ConversationMessage.conversation_id == conversation_id
        )
        result = self.db.execute(stmt).scalar()
        next_sequence = (result or 0) + 1
        
        # 创建新消息
        message = ConversationMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence=next_sequence
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_messages(self, conversation_id: str) -> List[ConversationMessage]:
        stmt = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.sequence)
        
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def get_chat_history(self, conversation_id: str) -> PostgresChatMessageHistory:
        return PostgresChatMessageHistory(conversation_id=conversation_id, session=self.db)
    
    def process_chat(self, conversation_id: str, user_message: str, model_type: int) -> str:
        # 获取对话，如果不存在则创建
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            conversation = self.create_conversation(
                title=user_message[:50] + "..." if len(user_message) > 50 else user_message
            )
        
        # 获取聊天历史
        chat_history = self.get_chat_history(str(conversation.id))
        
        # 添加用户消息
        chat_history.add_user_message(user_message)
        
        # 使用RAG服务生成回复
        from service.rag_service import RAGService
        rag_service = RAGService()
        prompt = rag_service.generate_rag_prompt(user_message, model_type)
        
        # 添加AI回复
        chat_history.add_ai_message(prompt)
        
        return prompt
    
    def create_conversation_with_timestamp(self, title: str, metadata: Optional[Dict[str, Any]] = None, created_at: Optional[datetime] = None) -> Conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            title=title,
            meta_data=metadata or {}
        )
        
        if created_at:
            conversation.created_at = created_at
            conversation.updated_at = created_at
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def update_conversation_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
            
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation 