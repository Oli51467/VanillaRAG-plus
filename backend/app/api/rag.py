from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_service import RAGService

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