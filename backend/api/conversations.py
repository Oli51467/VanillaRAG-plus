from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from db.database import get_db
from service.conversation_service import ConversationService

router = APIRouter()

# 请求和响应模型
class ConversationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    title: str = Field(..., description="对话标题")
    model_type: int = Field(1, description="模型类型 (1=DeepSeek, 2=Qwen)")
    metadata: Optional[dict] = Field(None, description="元数据")

class ConversationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    model_type: int = Field(..., description="模型类型")
    metadata: Optional[dict] = Field(None, description="元数据")

class ConversationList(BaseModel):
    conversations: List[ConversationResponse] = Field(..., description="对话列表")
    total: int = Field(..., description="总数")

class MessageCreate(BaseModel):
    content: str = Field(..., description="消息内容")
    role: str = Field("human", description="角色 (human, ai, system)")

class MessageResponse(BaseModel):
    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="对话ID")
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")
    created_at: str = Field(..., description="创建时间")
    sequence: int = Field(..., description="序列号")

class MessageList(BaseModel):
    messages: List[MessageResponse] = Field(..., description="消息列表")

class ChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    message: str = Field(..., description="用户消息")
    model_type: int = Field(1, description="模型类型 (1=DeepSeek, 2=Qwen)")

class ChatResponse(BaseModel):
    conversation_id: str = Field(..., description="对话ID")
    response: str = Field(..., description="AI回复")

class ConversationUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    title: str = Field(..., description="对话标题")

# API端点
@router.post("/", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    service = ConversationService(db)
    
    # 检查元数据中是否包含原始创建时间
    original_created_at = None
    if conversation.metadata and 'original_created_at' in conversation.metadata:
        try:
            from datetime import datetime
            original_created_at = datetime.fromisoformat(conversation.metadata['original_created_at'].replace('Z', '+00:00'))
            # 从元数据中移除original_created_at，因为它已经被使用
            conversation.metadata.pop('original_created_at')
        except (ValueError, TypeError) as e:
            print(f"无法解析原始创建时间: {e}")
    
    # 使用适当的方法创建对话
    if original_created_at:
        new_conversation = service.create_conversation_with_timestamp(
            title=conversation.title,
            model_type=conversation.model_type,
            metadata=conversation.metadata,
            created_at=original_created_at
        )
    else:
        new_conversation = service.create_conversation(
            title=conversation.title,
            model_type=conversation.model_type,
            metadata=conversation.metadata
        )
    
    return ConversationResponse(**new_conversation.to_dict())

@router.get("/", response_model=ConversationList)
async def list_conversations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    service = ConversationService(db)
    conversations = service.list_conversations(limit=limit, offset=offset)
    
    # 获取总数
    total = len(service.list_conversations(limit=10000))
    
    return ConversationList(
        conversations=[ConversationResponse(**conv.to_dict()) for conv in conversations],
        total=total
    )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    service = ConversationService(db)
    conversation = service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return ConversationResponse(**conversation.to_dict())

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    service = ConversationService(db)
    success = service.delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return {"message": "对话已删除"}

@router.get("/{conversation_id}/messages", response_model=MessageList)
async def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = conversation_service.get_conversation_messages(conversation_id)
    
    return MessageList(messages=[MessageResponse(**msg.to_dict()) for msg in messages])


@router.post("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation_title(conversation_id: str, update_data: ConversationUpdate, db: Session = Depends(get_db)):
    service = ConversationService(db)
    conversation = service.update_conversation_title(conversation_id, update_data.title)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return ConversationResponse(**conversation.to_dict()) 