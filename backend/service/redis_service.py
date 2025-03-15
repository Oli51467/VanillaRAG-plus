from utils.logger import logger
import redis

class RedisManager:

    def __init__(self, host, port, password, file_hashes_key):
        self.client = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        self.file_hashes_key = file_hashes_key

    def get_existing_file_hashes(self):
        """从 Redis 获取所有已存在的文件哈希值。"""
        existing_hashes = self.client.hgetall(self.file_hashes_key)
        logger.info(f"已记录的文件哈希总数：{len(existing_hashes)}")
        return existing_hashes

    def update_existing_file_hashes(self, file_hashes):
        """批量更新 Redis 中的文件哈希值。"""
        if file_hashes:
            with self.client.pipeline() as pipe:
                pipe.hset(self.file_hashes_key, mapping=file_hashes)
                pipe.execute()
            logger.info(f"已更新 {len(file_hashes)} 个文件哈希到 Redis。")

    def delete_file_hashes(self, keys):
        """批量从 Redis 删除文件哈希值。"""
        if keys:
            with self.client.pipeline() as pipe:
                pipe.hdel(self.file_hashes_key, *keys)
                pipe.execute()
            logger.info(f"已从 Redis 删除 {len(keys)} 个文件哈希")