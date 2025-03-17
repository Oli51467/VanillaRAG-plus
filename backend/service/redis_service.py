from utils.logger import logger
import redis
from service.config import Config

class RedisService:

    def __init__(self, host, port, password, document_key):
        self.client = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        self.document_key = document_key
        logger.info("Successfully connected to Redis")

    def get_disabled_document(self):
        # 获取self.document_uuid_key为key的Set中的所有元素
        disabled_documents = self.client.smembers(self.document_key)
        logger.info(f"不检索的文件数量：{len(disabled_documents)}")
        return disabled_documents

    def update_disabled_document(self, document_uuid):
        if document_uuid:
            if self.client.sismember(self.document_key, document_uuid):
                self.client.srem(self.document_key, document_uuid)
            else:
                self.client.sadd(self.document_key, document_uuid)
        logger.info(f"已更新文件 {document_uuid} 的状态")

redis_service = RedisService(host=Config.REDIS_HOST, port=Config.REDIS_PORT, password=Config.REDIS_PASSWORD, document_key=Config.REDIS_KEY)