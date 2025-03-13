# -*- coding: utf-8 -*-

from typing import List
from pymilvus import MilvusClient, MilvusException, FieldSchema, CollectionSchema, DataType, Collection, AnnSearchRequest, WeightedRanker
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus.model.reranker import BGERerankFunction
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
        # 定义字段
        fields = [
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),  # 文档唯一标识
            FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=256),  # 文档名称
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=8192),  # 文本块内容
            FieldSchema(name="dense_embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),       # 向量维度根据模型调整
            FieldSchema(name="sparse_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR)  # 稀疏向量
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
                field_name="dense_embedding",
                index_name="dense_embedding_index",
                index_type="IVF_FLAT",
                metric_type="COSINE",
                params={ "nlist": 128 }
            )

            index_params.add_index(
                field_name="sparse_embedding",
                index_name="sparse_embedding_index",
                index_type="SPARSE_WAND",
                metric_type="IP",
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
        sparse_matrix = vectors['sparse']  # 假设这是scipy.sparse矩阵
        
        for i in range(len(chunks)):
            # 获取当前稀疏向量行
            row = sparse_matrix.getrow(i).tocoo()
            
            # 转换为Milvus支持的字典格式
            sparse_dict = {int(col): float(val) for col, val in zip(row.col, row.data)}
            
            data.append({
                "document_id": str(kwargs['document_uuid']),
                "document_name": str(kwargs['document_name']),
                "chunk_text": chunks[i],
                "dense_embedding": vectors['dense'][i],
                "sparse_embedding": sparse_dict
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

    def search_by_vector(self, vector, collection_name, limit=5):
        #先加载集合到内存
        self.client.load_collection(collection_name=collection_name, timeout=100000)

        # 准备混合搜索参数
        dense_search_params = {"metric_type": "COSINE", "params": {}}
        dense_search_req = AnnSearchRequest(
            data=vector['dense'],
            anns_field="dense_embedding",
            param=dense_search_params,
            limit=limit,
        )
        sparse_search_params = {"metric_type": "IP", "params": {}}
        sparse_search_req = AnnSearchRequest(
            data=vector['sparse'],
            anns_field="sparse_embedding",
            param=sparse_search_params,
            limit=limit,
        )
        reranker = WeightedRanker(1.0, 1.0)
        res = self.client.hybrid_search(
            collection_name=collection_name,
            reqs=[dense_search_req, sparse_search_req],
            ranker=reranker,
            limit=limit,
            output_fields=["document_id", "chunk_text", "document_name"],
        )
        return res[0]

    def search_by_id(self, collection_name, id, output_fields=["id", "text"]):
        res = self.client.get(collection_name, id, output_fields=output_fields)
        return res