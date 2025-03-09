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
    model_type: int = Field(1, description="选择的大模型类型：1表示DeepSeek，2表示Qwen")
    top_k: int = Field(5, description="检索的文档数量，默认为5")


class RAGResponse(BaseModel):
    """RAG响应模型"""
    prompt: str = Field(..., description="生成的完整提示文本")
    model_type: int = Field(..., description="使用的大模型类型")
    documents_count: int = Field(..., description="检索到的文档数量")


class RAGChatRequest(BaseModel):
    """RAG聊天请求模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    query: str = Field(..., description="用户输入的查询文本")
    model_type: int = Field(1, description="选择的大模型类型：1表示DeepSeek，2表示Qwen")
    top_k: int = Field(5, description="检索的文档数量，默认为5")
    conversation_id: Optional[str] = Field(None, description="对话ID，如果为空则创建新对话")


class RAGChatResponse(BaseModel):
    """RAG聊天响应模型"""
    prompt: str = Field(..., description="生成的完整提示文本")
    model_type: int = Field(..., description="使用的大模型类型")
    documents_count: int = Field(..., description="检索到的文档数量")
    conversation_id: str = Field(..., description="对话ID")
    message_id: str = Field(..., description="消息ID")


@router.post("/generate_prompt", response_model=RAGResponse)
async def generate_rag_prompt(rag_request: RAGRequest):
    """
    生成RAG提示
    
    该接口根据用户输入检索相关文档，并生成适合发送给选定大模型的完整提示。
    """
    try:
        # 检查模型类型是否有效
        if rag_request.model_type not in [1, 2]:
            raise HTTPException(status_code=400, detail="无效的模型类型，必须是1(DeepSeek)或2(Qwen)")
        
        # 检查top_k参数是否有效
        top_k = min(max(1, rag_request.top_k), 10)  # 限制在1-10之间
        
        # 生成提示
        prompt = rag_service.generate_rag_prompt(
            query=rag_request.query,
            model_type=rag_request.model_type,
            top_k=top_k
        )
        
        # 获取检索到的文档数量
        # 先检索文档，不过这里会重复调用，可以在实际场景中优化
        docs_with_scores = rag_service.retrieve_relevant_documents(
            rag_request.query, 
            rag_request.model_type, 
            top_k
        )
        documents_count = len(docs_with_scores)
        
        return RAGResponse(
            prompt=prompt,
            model_type=rag_request.model_type,
            documents_count=documents_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成RAG提示失败: {str(e)}")


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(
    rag_request: RAGChatRequest,
    db: Session = Depends(get_db)
):
    """
    RAG聊天接口
    
    该接口根据用户输入检索相关文档，生成提示，并保存对话历史。
    """
    try:
        # 检查模型类型是否有效
        if rag_request.model_type not in [1, 2]:
            raise HTTPException(status_code=400, detail="无效的模型类型，必须是1(DeepSeek)或2(Qwen)")
        
        # 检查top_k参数是否有效
        top_k = min(max(1, rag_request.top_k), 10)  # 限制在1-10之间
        
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
                title=title,
                model_type=rag_request.model_type
            )
            conversation_id = str(conversation.id)
        
        # 添加用户消息
        user_message = conversation_service.add_message(
            conversation_id=conversation_id,
            role="human",
            content=rag_request.query
        )
        
        # 生成RAG提示
        prompt = rag_service.generate_rag_prompt(
            query=rag_request.query,
            model_type=rag_request.model_type,
            top_k=top_k
        )
        
        # 添加系统回复
        ai_message = conversation_service.add_message(
            conversation_id=conversation_id,
            role="ai",
            content=prompt
        )
        
        # 获取检索到的文档数量
        docs_with_scores = rag_service.retrieve_relevant_documents(
            rag_request.query, 
            rag_request.model_type, 
            top_k
        )
        documents_count = len(docs_with_scores)
        
        return RAGChatResponse(
            prompt=prompt,
            model_type=rag_request.model_type,
            documents_count=documents_count,
            conversation_id=conversation_id,
            message_id=str(ai_message.id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG聊天失败: {str(e)}") 