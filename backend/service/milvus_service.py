# -*- coding: utf-8 -*-

from typing import List
from pymilvus import MilvusClient, MilvusException, FieldSchema, CollectionSchema, DataType, Collection
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from service.logger import logger
from service.config import Config


class M3EEmbeddings():
    def __init__(self):
        self.embedding_function = BGEM3EmbeddingFunction(
            model_name=Config.EMBEDDING_MODEL,
            use_fp16=False,
            batch_size=5,
            device='cpu'
        )

    def encode_documents(self, content: List[str]) -> List[float]:
        """将文本转换为向量"""
        return self.embedding_function.encode_documents(content)
    
    
class MilvusService:
    def __init__(self):
        """初始化Milvus服务"""
        if not self.connect_to_milvus():
            raise ConnectionError("Failed to connect to Milvus")
        self.embedding_model = M3EEmbeddings()

    def connect_to_milvus(self):
        try:
            self.client = MilvusClient(uri=Config.MILVUS_SERVER, user=Config.MILVUS_USER,
            password=Config.MILVUS_PASSWORD)
            self.client.list_collections()
            print("Successfully connected to Milvus")
            return True
        except MilvusException as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
        
    def get_collection_names(self):
        return self.client.list_collections()
    
    def get_collections(self):
        collections_name = self.client.list_collections()
        collections = []
        for collection_name in collections_name:
            collection = self.get_collection_info(collection_name)
            collections.append(collection)
        return collections
    
    def get_collection_info(self, collection_name):
        collection = self.client.describe_collection(collection_name)
        collection.update(self.client.get_collection_stats(collection_name))
        return collection
    
    def create_collection(self, collection_name, dimension=None):
        if self.client.has_collection(collection_name=collection_name):
            # collection = Collection(collection_name)
            # if not collection.has_index():
            #     self.create_index(collection_name)
            return
        # 定义字段
        fields = [
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),  # 文档唯一标识
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=8192),  # 文本块内容
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)       # 向量维度根据模型调整
        ]
        # 创建 Collection
        schema = CollectionSchema(fields, description="Document chunks")
        self.client.create_collection(
            collection_name=collection_name,
            dimension=dimension,
            schema=schema
        )
        self.create_index(collection_name)

    def create_index(self, collection_name):
        try:
            index_params =self.client.prepare_index_params()

            index_params.add_index(
                field_name="embedding",
                index_name="vector_index",
                index_type="IVF_FLAT",
                metric_type="COSINE",
                params={ "nlist": 128 }
            )
            
            # 为向量字段创建索引
            self.client.create_index(
                collection_name=collection_name,
                index_params=index_params,
                sync=False
            )
            
            logger.info(f"为集合 {collection_name} 创建索引成功")
            return True
        except Exception as e:
            logger.error(f"为集合 {collection_name} 创建索引失败: {e}")
            return False
        

    def add_documents(self, chunks, collection_name, **kwargs):
        if self.client.has_collection(collection_name=collection_name):
            logger.error(f"Collection {collection_name} not found, create it")
            return

        # 生成文本的向量嵌入
        vectors = self.embedding_model.encode_documents(chunks)

        data = [
            {
                "document_id": str(kwargs["document_uuid"]),        # 文档ID
                "chunk_text": chunks[i],                            # 文本块
                "embedding": vectors['dense'][i]                    # 向量嵌入
            }
            for i in range(len(chunks))
        ]
        
        try:
            res = self.client.insert(collection_name=collection_name, data=data)
            logger.info(f"成功向{collection_name}插入{len(data)}条记录")
            return res
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            raise
    
    def delete_documents(self, collection_name, document_uuid):
        try:
            # 检查集合是否存在
            if not self.client.has_collection(collection_name=collection_name, timeout=100000):
                logger.warning(f"集合 {collection_name} 不存在，无法删除")
                return {"delete_count": 0}
                
            #先加载集合到内存
            self.client.load_collection(collection_name=collection_name, timeout=100000)
            logger.info("已加载到内存")
            
            # 执行删除操作
            res = self.client.delete(collection_name=collection_name, filter=f"document_id == '{document_uuid}'",timeout=100000)
            logger.info("已从集合中删除文档")
            
            # 操作完成后释放集合
            self.client.release_collection(collection_name=collection_name, timeout=100000)
            logger.info("集合已从内存释放")
            
            return res
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            # 确保发生错误时也释放集合
            try:
                self.client.release_collection(collection_name=collection_name)
            except:
                pass
            raise

    def search(self, query, collection_name, limit=3):
        query_vectors = self.embed_model.batch_encode([query])
        return self.search_by_vector(query_vectors[0], collection_name, limit)

    def search_by_vector(self, vector, collection_name, limit=3):
        res = self.client.search(
            collection_name=collection_name,  # target collection
            data=[vector],  # query vectors
            limit=limit,  # number of returned entities
            output_fields=["text", "file_id"],  # specifies fields to be returned
        )

        return res[0]

    def examples(self, collection_name, limit=20):
        res = self.client.query(
            collection_name=collection_name,
            limit=10,
            output_fields=["id", "text"],
        )
        return res

    def search_by_id(self, collection_name, id, output_fields=["id", "text"]):
        res = self.client.get(collection_name, id, output_fields=output_fields)
        return res
        
        
if __name__ == "__main__":
    config = Config()
    milvus_service = MilvusService()
    print(milvus_service.get_collection_names())
