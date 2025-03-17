# -*- coding: utf-8 -*-
import os
import uuid
import re
from datetime import datetime, timezone

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, update
from langchain.text_splitter import RecursiveCharacterTextSplitter

import docx2txt
from pypdf import PdfReader

from service.config import Config
from db.models import Document
from utils.logger import logger
import utils.document_util as document_util
from service.milvus_service import milvus_service

class DocumentService:
    def __init__(self, db: Session):
        # 使用M3E嵌入模型替代简单嵌入模型
        self.db = db
        self.milvus_service = milvus_service
    
    def allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    def save_document(self, file, file_path, file_uuid) -> Document:
        file_extension = file_path.split('.')[-1].lower()
        _, _, file_hash = document_util.calculate_file_hash(file_path)
        
        document = Document(
            id=file_uuid,
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            file_type=file_extension,
            file_hash=file_hash,
            upload_time=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        logger.info(f"文档已保存到数据库: {document.file_name}")
        # 删除文件
        os.remove(file_path)
        return document
    
    def get_all_documents(self) -> List[Document]:
        stmt = select(Document).order_by(desc(Document.upload_time))
        result = self.db.execute(stmt).scalars().all()
        return result
    
    def get_document_by_hash(self, file_hash: str) -> bool:
        stmt = select(Document).where(Document.file_hash == file_hash)
        result = self.db.execute(stmt).scalars().first()
        return result is not None
    
    def update_document_status(self, doc_id: str, status: int) -> bool:
        stmt = update(Document).where(Document.id == doc_id).values(status=status)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
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
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_extension == 'docx' or file_extension == 'doc':
                # 处理DOCX文件
                text = docx2txt.process(file_path)
                return text if text else "DOCX文件无法提取文本内容"
        
            #替换掉连续的空格、换行符和制表符
            text = re.sub(r'\s+', ' ', text)
            # 去除首尾空格
            text = text.strip()
        except Exception as e:
            logger.error(f"提取文档失败: {str(e)}")
            return f"文件处理失败: {str(e)}"
    
    def process_document(self, file, chunk_size, overlap_size, embedding_model) -> Document:
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

            # 查询文件哈希值，是否已经上传
            _, _,file_hash = document_util.calculate_file_hash(file_path)

            if self.get_document_by_hash(file_hash):
                logger.info(f"文件已存在: {file.filename}")
                os.remove(file_path)
                return None

            # 根据文档类型提取文本
            text = self.extract_text(file_path)
            logger.info(f"成功提取文档，文本长度: {len(text)}")

            # 分割文本
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap_size)
            chunks = self.text_splitter.split_text(text)
            logger.info(f"文本分割完成，共 {len(chunks)} 个块")
            
            # 将文档添加到向量数据库
            self.milvus_service.create_collection(Config.MILVUS_COLLECTION_NAME, dimension=1024)
            # 向量化并存储
            self.milvus_service.add_documents(chunks=chunks, collection_name=Config.MILVUS_COLLECTION_NAME, document_uuid=document_uuid, document_name=file.filename)
            logger.info("文档已存储至向量数据库")
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
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