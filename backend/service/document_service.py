# -*- coding: utf-8 -*-
import os
import uuid
from datetime import datetime, timezone

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc
from langchain.text_splitter import RecursiveCharacterTextSplitter

import docx2txt
from pypdf import PdfReader

from service.milvus_service import MilvusService
from service.config import Config
from db.models import Document
from utils.logger import logger


example_docs = [
    'information retrieval is a field of study.',
    'information retrieval focuses on finding relevant information in large datasets.',
    'data mining and information retrieval overlap in research.'
]

class DocumentService:
    def __init__(self, db: Session):
        # 使用M3E嵌入模型替代简单嵌入模型
        self.db = db
        self.milvus_service = MilvusService()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=80, chunk_overlap=5)
    
    def allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    def save_document(self, file, file_path, file_uuid) -> Document:
        file_extension = file_path.split('.')[-1].lower()
        
        document = Document(
            id=file_uuid,
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            file_type=file_extension,
            upload_time=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def get_all_documents(self) -> List[Document]:
        stmt = select(Document).order_by(desc(Document.upload_time))
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def delete_document(self, doc_id: str) -> bool:
        try:
            self.milvus_service.delete_documents(Config.MILVUS_COLLECTION_NAME, doc_id)
        except Exception as e:
            logger.error(f"删除向量数据库失败: {str(e)}")
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
            
            elif file_extension == 'docx' or file_extension == 'doc':
                # 处理DOCX文件
                text = docx2txt.process(file_path)
                return text if text else "DOCX文件无法提取文本内容"
            
        except Exception as e:
            logger.error(f"提取文档失败: {str(e)}")
            return f"文件处理失败: {str(e)}"
    
    def process_document(self, file) -> Document:
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
            logger.info(f"成功提取文档，文本长度: {len(text)}")
            
            if text and len(text.strip()) > 100:
                # 分割文本
                chunks = self.text_splitter.split_text(text)
                logger.info(f"文本分割完成，共 {len(chunks)} 个块")
                
                # 将文档添加到向量数据库
                self.milvus_service.create_collection(Config.MILVUS_COLLECTION_NAME, dimension=1024)
                # 向量化并存储
                self.milvus_service.add_documents(chunks=chunks, collection_name=Config.MILVUS_COLLECTION_NAME, document_uuid=document_uuid, document_name=file.filename)
                logger.info("文档已存储至向量数据库")
        except Exception as e:
            logger.error(f"文档保存至向量数据库失败: {str(e)}")
            raise e
        # 保存文档
        document = self.save_document(file, file_path, document_uuid)
        return document

    async def retrieve(self, query: str, top_k: int = 5) -> List[tuple]:
        # Step1:查询向量化
        query_vectors = self.milvus_service.embedding_model.encode_query([query])

        # Step2:混合检索
        hit_results = self.milvus_service.search_by_vector(query, query_vectors, Config.MILVUS_COLLECTION_NAME, top_k)

        # Step3:重排序
        result_texts = [hit.get('entity').get("chunk_text") for hit in hit_results]  # 文本内容
        content2doc_name = {hit.get('entity').get("chunk_text"): hit.get('entity').get("document_name") for hit in hit_results}  # 文本内容到文档名称的映射

        results = self.milvus_service.reranker(query, result_texts, top_k=top_k)
        doc_names = [content2doc_name.get(hit.text) for hit in results if content2doc_name.get(hit.text)]
        unique_doc_names = list(dict.fromkeys(doc_names))
        references = unique_doc_names
        # Step4:返回结果
        return  [
                    {
                        "text": hit.text,
                        "score": hit.score,
                        "doc_name": content2doc_name.get(hit.text)
                    } for hit in results
                ], references