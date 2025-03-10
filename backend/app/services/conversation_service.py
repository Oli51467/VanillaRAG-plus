from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, func
import uuid
from datetime import datetime

from app.db.models import Conversation, ConversationMessage
from app.services.chat_history import PostgresChatMessageHistory
from app.services import get_document_service

class ConversationService:
    """对话管理服务"""
    
    def __init__(self, db: Session):
        """
        初始化对话服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.document_service = get_document_service()
    
    def create_conversation(self, title: str, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        创建新对话
        
        Args:
            title: 对话标题
            metadata: 元数据
            
        Returns:
            新创建的对话
        """
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
        """
        获取对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话对象，如果不存在则返回None
        """
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result
    
    def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """
        获取对话列表
        
        Args:
            limit: 返回的最大数量
            offset: 偏移量
            
        Returns:
            对话列表
        """
        stmt = select(Conversation).order_by(desc(Conversation.created_at)).limit(limit).offset(offset)
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功删除
        """
        # 先删除消息
        msg_stmt = delete(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id)
        self.db.execute(msg_stmt)
        
        # 再删除对话
        conv_stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = self.db.execute(conv_stmt)
        
        self.db.commit()
        
        return result.rowcount > 0
    
    def add_message(self, conversation_id: str, role: str, content: str) -> ConversationMessage:
        """
        添加消息
        
        Args:
            conversation_id: 对话ID
            role: 角色 (human, ai, system)
            content: 消息内容
            
        Returns:
            新创建的消息
        """
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
        """
        获取对话消息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            消息列表
        """
        stmt = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.sequence)
        
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def get_chat_history(self, conversation_id: str) -> PostgresChatMessageHistory:
        """
        获取LangChain聊天历史
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            聊天历史对象
        """
        return PostgresChatMessageHistory(conversation_id=conversation_id, session=self.db)
    
    def process_chat(self, conversation_id: str, user_message: str, model_type: int) -> str:
        """
        处理聊天消息
        
        Args:
            conversation_id: 对话ID
            user_message: 用户消息
            model_type: 模型类型
            
        Returns:
            AI回复
        """
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
        from app.services.rag_service import RAGService
        rag_service = RAGService()
        prompt = rag_service.generate_rag_prompt(user_message, model_type)
        
        # 添加AI回复
        chat_history.add_ai_message(prompt)
        
        return prompt
    
    def create_conversation_with_timestamp(self, title: str, metadata: Optional[Dict[str, Any]] = None, created_at: Optional[datetime] = None) -> Conversation:
        """
        创建新对话，并允许指定创建时间
        
        Args:
            title: 对话标题
            metadata: 元数据
            created_at: 创建时间，如果为None则使用当前时间
            
        Returns:
            新创建的对话
        """
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
        """
        更新对话标题
        
        Args:
            conversation_id: 对话ID
            title: 新标题
            
        Returns:
            更新后的对话，如果不存在则返回None
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
            
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation 