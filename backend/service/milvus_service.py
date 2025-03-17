# -*- coding: utf-8 -*-

from typing import List
from pymilvus import MilvusClient, MilvusException, DataType, AnnSearchRequest, RRFRanker, Function, FunctionType
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus.model.reranker import BGERerankFunction
from utils.logger import logger
from service.config import Config


class M3EEmbeddings():
    def __init__(self):
        self.embedding_function = BGEM3EmbeddingFunction(
            model_name=Config.EMBEDDING_MODEL,
            use_fp16=False,
            device='cpu'
        )

    def encode_documents(self, content: List[str]) -> List[float]:
        return self.embedding_function.encode_documents(content)
    
    def encode_query(self, content: List[str]) -> List[float]:
        return self.embedding_function.encode_queries(content)
    
    
class MilvusService:
    def __init__(self):
        if not self.connect_to_milvus():
            raise ConnectionError("Failed to connect to Milvus")
        # 嵌入模型
        self.embedding_model = M3EEmbeddings()  
        # 重排序模型
        self.reranker = (
            BGERerankFunction(model_name=Config.RERANKING_MODEL, device='cpu')
        )

    def connect_to_milvus(self):
        try:
            self.client = MilvusClient(uri=Config.MILVUS_SERVER, user=Config.MILVUS_USER,
            password=Config.MILVUS_PASSWORD)
            self.client.list_collections()
            logger.info("Successfully connected to Milvus")
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
            #self.client.drop_collection(collection_name)
            return

        schema = self.client.create_schema()
        schema.add_field(field_name="chunk_id", datatype=DataType.VARCHAR, is_primary=True, max_length=256)
        schema.add_field(field_name="document_id", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="document_name", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="chunk_text", datatype=DataType.VARCHAR, max_length=4096, enable_analyzer=True)
        schema.add_field(field_name="dense_embedding", datatype=DataType.FLOAT_VECTOR, dim=dimension)
        schema.add_field(field_name="sparse_embedding", datatype=DataType.SPARSE_FLOAT_VECTOR)

        bm25_function = Function(
            name="text_bm25_emb", # Function name
            input_field_names=["chunk_text"], # Name of the VARCHAR field containing raw text data
            output_field_names=["sparse_embedding"], # Name of the SPARSE_FLOAT_VECTOR field reserved to store generated embeddings
            function_type=FunctionType.BM25,
        )

        schema.add_function(bm25_function)
        
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
                field_name="dense_embedding",
                index_name="dense_embedding_index",
                index_type="AUTOINDEX",
                metric_type="COSINE",
            )

            index_params.add_index(
                field_name="sparse_embedding",
                index_name="sparse_embedding_index",
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="BM25",
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
        if not self.client.has_collection(collection_name=collection_name):
            logger.error(f"Collection {collection_name} not found, create it")
            self.create_collection(collection_name)

        # 生成文本的向量嵌入
        vectors = self.embedding_model.encode_documents(chunks)

        # 准备数据
        data = []
        for i in range(len(chunks)):
            # 为每个块生成唯一的ID，避免主键冲突
            chunk_id = f"{kwargs['document_uuid']}_{i}"
            data.append({
                "chunk_id": chunk_id,  # 修改为块级唯一ID
                "document_id": str(kwargs['document_uuid']),  # 保存原始文档ID
                "document_name": str(kwargs['document_name']),
                "chunk_text": chunks[i],
                "dense_embedding": vectors['dense'][i],
            })
        
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
            
            # 执行删除操作，使用document_id作为过滤条件
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

    def search_by_vector(self, query, query_vector, collection_name, limit=5):
        #先加载集合到内存
        self.client.load_collection(collection_name=collection_name, timeout=100000)

        # 准备混合搜索参数
        dense_search_params = {
            "data": query_vector['dense'],
            "anns_field": "dense_embedding",
            "param": {
                "metric_type": "COSINE",
            },
            "limit": limit
        }
        sparse_search_params = {
            "data": [query],
            "anns_field": "sparse_embedding",
            "param": {
                "metric_type": "BM25",
                "params": {"drop_ratio_build": 0.0}
            },
            "limit": limit
        }
        dense_search_req = AnnSearchRequest(**dense_search_params)
        sparse_search_req = AnnSearchRequest(**sparse_search_params)

        ranker = RRFRanker()
        res = self.client.hybrid_search(
            collection_name=collection_name,
            reqs=[dense_search_req, sparse_search_req],
            ranker=ranker,
            limit=limit,
            output_fields=["document_id", "chunk_text", "document_name"],
        )
        return res[0]
    

milvus_service = MilvusService()