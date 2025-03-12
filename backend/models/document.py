from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class DocumentBase(BaseModel):
    """文档基本信息"""
    file_name: str
    file_size: int
    upload_time: datetime


class DocumentCreate(DocumentBase):
    """创建文档的请求模型"""
    file_path: str
    id: str


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: str
    file_type: str  # 添加文件类型字段
    file_path: Optional[str] = None
    
    class Config:
        from_attributes = True  # 允许直接从ORM模型转换


class DocumentList(BaseModel):
    """文档列表响应模型"""
    documents: List[DocumentResponse] 