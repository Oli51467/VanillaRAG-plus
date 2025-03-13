from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, func
import uuid
from datetime import datetime, timezone

from db.models import Conversation, ConversationMessage

class ConversationService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, title: str) -> Conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            title=title,
            model_type=1,
            meta_data={},
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result
    
    def list_conversations(self) -> List[Conversation]:
        stmt = select(Conversation).order_by(desc(Conversation.created_at))
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
    
    def get_conversation_messages(self, conversation_id: str) -> List[ConversationMessage]:
        stmt = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.sequence)
        
        result = self.db.execute(stmt).scalars().all()
        return result
    
    
    def update_conversation_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
            
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation 