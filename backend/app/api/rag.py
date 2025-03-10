from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
import uuid

from app.services.rag_service import RAGService
from app.services.conversation_service import ConversationService
from app.db.database import get_db

router = APIRouter()
rag_service = RAGService()


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
async def rag_chat(
    rag_request: RAGChatRequest,
    db: Session = Depends(get_db)
):
    """
    RAG聊天接口
    
    该接口根据用户输入检索相关文档，生成提示，调用大模型获取回复，并保存对话历史。
    """
    try:
        
        # 创建对话服务
        conversation_service = ConversationService(db)
        
        # 获取或创建对话
        conversation_id = rag_request.conversation_id
        conversation = None
        
        if conversation_id:
            # 尝试获取现有对话
            conversation = conversation_service.get_conversation(conversation_id)
            
        if not conversation:
            # 创建新对话
            title = rag_request.query[:50] + "..." if len(rag_request.query) > 50 else rag_request.query
            conversation = conversation_service.create_conversation(
                title=title
            )
            conversation_id = str(conversation.id)
        
        # 添加用户消息
        conversation_service.add_message(
            conversation_id=conversation_id,
            role="human",
            content=rag_request.query
        )
        
        # 获取RAG响应
        rag_response = rag_service.get_rag_response(
            query=rag_request.query,
            model=rag_request.model,
        )
        
        # 添加AI回复
        ai_message = conversation_service.add_message(
            conversation_id=conversation_id,
            role="ai",
            content=rag_response["response"]
        )
        
        return RAGChatResponse(
            prompt=rag_response["prompt"],
            response=rag_response["response"],
            documents_count=rag_response["documents_count"],
            conversation_id=conversation_id,
            message_id=str(ai_message.id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG聊天失败: {str(e)}") 