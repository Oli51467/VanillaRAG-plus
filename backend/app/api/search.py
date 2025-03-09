from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import get_document_service

router = APIRouter()
document_service = get_document_service()


class SearchQuery(BaseModel):
    """搜索查询模型"""
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    """搜索结果模型"""
    content: str
    metadata: Dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    """搜索响应模型"""
    results: List[SearchResult]
    query: str


@router.post("/", response_model=SearchResponse)
async def search_documents(search_query: SearchQuery):
    """
    搜索文档
    """
    try:
        # 获取查询文本
        query = search_query.query
        top_k = min(search_query.top_k, 10)  # 限制最多返回10个结果
        
        # 使用向量数据库进行搜索
        docs_with_scores = document_service.search_documents(query, top_k)
        
        # 构建响应
        results = []
        for doc, score in docs_with_scores:
            results.append(
                SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=score
                )
            )
        
        return SearchResponse(results=results, query=query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}") 