import os
import uuid
from typing import List, Dict, Any, Optional
import docx2txt
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.schema.document import Document
from langchain.docstore.document import Document as LangchainDocument
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer

from app.core.config import UPLOAD_DIR, VECTOR_DB_PATH, ALLOWED_EXTENSIONS


class M3EEmbeddings(Embeddings):
    """使用M3E模型进行向量嵌入"""
    
    def __init__(self, model_name='moka-ai/m3e-base'):
        self.model = SentenceTransformer('moka-ai/m3e-base')
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """将文本转换为向量"""
        # 确保文本不为空
        processed_texts = []
        for text in texts:
            if not text or len(text.strip()) == 0:
                text = "空文本"
            processed_texts.append(text)
        
        # 使用M3E模型进行向量化
        vectors = self.model.encode(processed_texts, convert_to_numpy=True).tolist()
        return vectors
    
    def embed_query(self, text: str) -> List[float]:
        """将查询文本转换为向量"""
        if not text or len(text.strip()) == 0:
            text = "空文本"
        return self.model.encode(text, convert_to_numpy=True).tolist()
    
    # 添加__call__方法，使对象可调用
    def __call__(self, text: str) -> List[float]:
        """使对象可调用，返回文本的嵌入向量"""
        return self.embed_query(text)


class DocumentService:
    def __init__(self):
        # 使用M3E嵌入模型替代简单嵌入模型
        self.embeddings = M3EEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        # 确保向量数据库目录存在
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        
        # 尝试加载现有的向量数据库，如果不存在则创建新的
        try:
            self.vector_db = FAISS.load_local(VECTOR_DB_PATH, self.embeddings)
            print("成功加载现有向量数据库")
        except Exception as e:
            print(f"加载向量数据库失败: {str(e)}")
            # 创建一个空的文档列表
            empty_docs = [LangchainDocument(page_content="初始化文档", metadata={"source": "初始化"})]
            # 创建一个新的向量数据库
            self.vector_db = FAISS.from_documents(empty_docs, self.embeddings)
            # 保存向量数据库
            self.vector_db.save_local(VECTOR_DB_PATH)
            print("创建并保存了新的向量数据库")
    
    def allowed_file(self, filename: str) -> bool:
        """检查文件类型是否允许上传"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def save_file(self, file) -> str:
        """保存上传的文件并返回文件路径"""
        # 确保上传目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 生成唯一的文件名
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        return file_path
    
    def extract_text(self, file_path: str) -> str:
        """从文件中提取文本"""
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
            
            else:
                return f"不支持的文件类型: {file_extension}"
        except Exception as e:
            print(f"提取文本失败: {str(e)}")
            return f"文件处理失败: {str(e)}"
    
    def process_document(self, file_path: str, metadata: Dict[str, Any]) -> List[str]:
        """处理文档并将其添加到向量数据库"""
        try:
            # 提取文本
            text = self.extract_text(file_path)
            print(f"成功提取文本，长度: {len(text)}")
            
            if not text or len(text.strip()) == 0:
                text = "文件内容为空"
                
            # 分割文本
            chunks = self.text_splitter.split_text(text)
            print(f"文本分割完成，共 {len(chunks)} 个块")
            
            if not chunks:
                chunks = ["文件内容为空或无法分割"]
            
            # 创建文档对象
            docs = []
            for i, chunk in enumerate(chunks):
                doc_metadata = metadata.copy()
                doc_metadata["chunk"] = i
                docs.append(LangchainDocument(page_content=chunk, metadata=doc_metadata))
            
            # 将文档添加到向量数据库
            print(f"开始添加 {len(docs)} 个文档到向量数据库")
            self.vector_db.add_documents(docs)
            print("文档添加成功")
            
            # 保存向量数据库
            self.vector_db.save_local(VECTOR_DB_PATH)
            print("向量数据库保存成功")
            
            return [doc.page_content for doc in docs]
        except Exception as e:
            print(f"处理文档失败: {str(e)}")
            try:
                # 创建一个包含错误信息的文档
                error_doc = LangchainDocument(
                    page_content=f"文档处理失败: {str(e)}",
                    metadata=metadata
                )
                # 使用embed_documents方法手动创建向量
                texts = [error_doc.page_content]
                metadatas = [error_doc.metadata]
                
                # 手动嵌入文本并添加到向量存储
                embeddings = self.embeddings.embed_documents(texts)
                self.vector_db.add_embeddings(texts, embeddings, metadatas)
                
                # 保存向量数据库
                self.vector_db.save_local(VECTOR_DB_PATH)
                print("错误文档添加成功")
                
                return texts
            except Exception as inner_e:
                print(f"添加错误文档也失败了: {str(inner_e)}")
                return [f"文档处理失败: {str(e)}，无法添加到向量数据库: {str(inner_e)}"]
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档的元数据"""
        # 获取向量数据库中的所有文档
        docs = self.vector_db.docstore._dict.values()
        
        # 提取唯一的文档（基于文件名）
        unique_docs = {}
        for doc in docs:
            if "source" in doc.metadata and "初始化" not in doc.metadata["source"]:
                file_name = doc.metadata.get("file_name", "")
                if file_name and file_name not in unique_docs:
                    unique_docs[file_name] = {
                        "id": doc.metadata.get("id", ""),
                        "file_name": file_name,
                        "file_path": doc.metadata.get("file_path", ""),
                        "upload_time": doc.metadata.get("upload_time", ""),
                        "file_size": doc.metadata.get("file_size", 0),
                    }
        
        return list(unique_docs.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """从向量数据库中删除文档"""
        # 获取向量数据库中的所有文档
        docs = list(self.vector_db.docstore._dict.values())
        
        # 找到要删除的文档
        docs_to_keep = []
        deleted = False
        
        for doc in docs:
            if doc.metadata.get("id") != doc_id:
                docs_to_keep.append(doc)
            else:
                deleted = True
                # 如果文件存在，删除文件
                file_path = doc.metadata.get("file_path", "")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
        
        if deleted:
            # 重新创建向量数据库
            if docs_to_keep:
                self.vector_db = FAISS.from_documents(docs_to_keep, self.embeddings)
                self.vector_db.save_local(VECTOR_DB_PATH)
            else:
                # 如果没有文档，创建一个空的向量数据库
                empty_docs = [LangchainDocument(page_content="初始化文档", metadata={"source": "初始化"})]
                self.vector_db = FAISS.from_documents(empty_docs, self.embeddings)
                self.vector_db.save_local(VECTOR_DB_PATH)
        
        return deleted
        
    def search_documents(self, query: str, top_k: int = 5) -> List[tuple]:
        """搜索文档"""
        # 使用向量数据库进行相似度搜索
        docs_with_scores = self.vector_db.similarity_search_with_score(query, k=top_k)
        
        # 返回文档和分数
        return docs_with_scores 