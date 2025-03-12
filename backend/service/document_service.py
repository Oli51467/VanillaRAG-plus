# -*- coding: utf-8 -*-
import os
import uuid
from datetime import datetime

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc
from langchain.text_splitter import RecursiveCharacterTextSplitter

import docx2txt
from pypdf import PdfReader

from service.milvus_service import MilvusService
from service.config import Config
from db.models import Document


class DocumentService:
    def __init__(self, db: Session):
        # 使用M3E嵌入模型替代简单嵌入模型
        self.db = db
        self.milvus_service = MilvusService()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    def allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    def save_document(self, file, file_path, file_uuid) -> Document:
        file_extension = file_path.split('.')[-1].lower()
        
        document = Document(
            id=file_uuid,
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            file_type=file_extension,
            upload_time=datetime.now().isoformat()
        )
        print("addId"+ str(file_uuid))
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        stmt = select(Document).order_by(desc(Document.upload_time)).limit(limit).offset(offset)
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def delete_document(self, doc_id: str) -> bool:
        try:
            self.milvus_service.delete_documents(Config.MILVUS_COLLECTION_NAME, doc_id)
        except Exception as e:
            print(f"删除向量数据库失败: {str(e)}")
            return False
        stmt = delete(Document).where(Document.id == doc_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def extract_text(self, file_path: str) -> str:
        file_extension = file_path.split('.')[-1].lower()
        try:
            if file_extension == 'pdf':
                # 处理PDF文件
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text if text else "PDF文件无法提取文本内容"
            
            elif file_extension == 'txt':
                # 处理TXT文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，尝试其他编码
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
            
            elif file_extension == 'docx':
                # 处理DOCX文件
                text = docx2txt.process(file_path)
                return text if text else "DOCX文件无法提取文本内容"
            
        except Exception as e:
            print(f"提取文本失败: {str(e)}")
            return f"文件处理失败: {str(e)}"
    
    def process_document(self, file) -> List[str]:

        try:
            # 确保上传目录存在
            os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
            
            document_uuid = uuid.uuid4()
            # 生成唯一的文件名
            file_name = f"{document_uuid}_{file.filename}"
            file_path = os.path.join(Config.UPLOAD_DIR, file_name)
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(file.file.read())

            # 根据文档类型提取文本
            text = self.extract_text(file_path)
            print(f"成功提取文本，长度: {len(text)}")
            
            if not text or len(text.strip()) == 0:
                text = "文件内容为空"
                
            # 分割文本
            chunks = self.text_splitter.split_text(text)
            print(f"文本分割完成，共 {len(chunks)} 个块")
            
            if not chunks:
                chunks = ["文件内容为空或无法分割"]
            
            # 将文档添加到向量数据库
            self.milvus_service.create_collection(Config.MILVUS_COLLECTION_NAME, dimension=1024)
            print("创建Milvus集合成功")

            # 向量化并存储
            self.milvus_service.add_documents(chunks=chunks, collection_name=Config.MILVUS_COLLECTION_NAME, document_uuid=document_uuid)
            print("向量数据库保存成功")
        except Exception as e:
            print(f"向量数据库保存失败: {str(e)}")
            raise e
        # 保存文档
        document = self.save_document(file, file_path, document_uuid)
        return document
        

    def search_documents(self, query: str, top_k: int = 5) -> List[tuple]:
        """搜索文档"""
        # 使用向量数据库进行相似度搜索
        # 多取几个结果，以便在过滤掉初始化文档后仍有足够的结果
        extended_top_k = top_k + 1
        docs_with_scores = self.vector_db.similarity_search_with_score(query, k=extended_top_k)
        
        # 过滤掉初始化文档
        filtered_results = []
        for doc, score in docs_with_scores:
            # 检查是否是初始化文档
            if "source" in doc.metadata and doc.metadata["source"] == "初始化":
                continue
            filtered_results.append((doc, score))
        
        # 确保不超过请求的top_k数量
        filtered_results = filtered_results[:top_k]
        
        # 返回文档和分数
        return filtered_results 