from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from service.rag_service import RAGService
from service.conversation_service import ConversationService
from db.database import get_db
from service.config import Config
from service.logger import logger

router = APIRouter()

class RAGRequest(BaseModel):
    """RAG请求模型"""
    query: str = Field(..., description="用户输入的查询文本")
    model: str = Field("Qwen/QwQ-32B", description="使用的模型名称")
    top_k: int = Field(5, description="检索的文档数量，默认为5")


class RAGResponse(BaseModel):
    """RAG响应模型"""
    prompt: str = Field(..., description="生成的完整提示文本")
    response: str = Field(..., description="大模型生成的回复")
    documents_count: int = Field(..., description="检索到的文档数量")


class RAGChatRequest(BaseModel):
    """RAG聊天请求模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    query: str = Field(..., description="用户输入的查询文本")
    model: str = Field("Qwen/QwQ-32B", description="使用的模型名称")
    top_k: int = Field(5, description="检索的文档数量，默认为5")
    conversation_id: Optional[str] = Field(None, description="对话ID，如果为空则创建新对话")


class RAGChatResponse(BaseModel):
    """RAG聊天响应模型"""
    prompt: str = Field(..., description="生成的完整提示文本")
    response: str = Field(..., description="大模型生成的回复")
    documents_count: int = Field(..., description="检索到的文档数量")
    conversation_id: str = Field(..., description="对话ID")
    message_id: str = Field(..., description="消息ID")


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(request: RAGChatRequest, db: Session = Depends(get_db)):
    rag_service = RAGService(db)
    try:
        # 创建对话服务
        conversation_service = ConversationService(db)
        # 获取或创建对话
        conversation_id = request.conversation_id
        conversation = None
        
        if conversation_id:
            # 尝试获取现有对话
            conversation = conversation_service.get_conversation(conversation_id)
            logger.info(f"获取现有对话: {conversation_id}")
            
        if not conversation:
            # 创建新对话
            title = request.query[:50] + "..." if len(request.query) > 50 else request.query
            conversation = conversation_service.create_conversation(
                title=title
            )
            conversation_id = str(conversation.id)
            logger.info(f"创建新对话: {conversation_id}")
        
        # 添加用户消息
        conversation_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.query
        )
        logger.info(f"添加用户消息, content: {request.query}")
        # RAG
        rag_response = await rag_service.non_streaming_workflow(
            conversation_id=conversation_id,
            user_query=request.query,
            model=request.model,
        )
        # 添加模型消息
        ai_message = conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=rag_response['response']
        )
        
        return RAGChatResponse(
            prompt=rag_response['prompt'],
            response=rag_response['response'],
            documents_count=rag_response['documents_count'],
            conversation_id=conversation_id,
            message_id=str(ai_message.id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG聊天失败: {str(e)}") 