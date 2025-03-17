import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    # 加载环境变量
    load_dotenv()

    # 基本路径
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    # 上传文件存储路径
    UPLOAD_DIR = os.path.join(BASE_DIR, "backend/uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # API配置
    API_PREFIX = "/api"
    API_V1_STR = "/v1"

    # 允许上传的文件类型
    ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "doc", "markdown"}

    # LLM相关配置
    LLM_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"                         # 接入LLM服务的基础URL                                          # 接入LLM服务的API_KEY，若无需验证可随便传
    LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"                                             # 接入LLM服务的模型选择，若无需验证可随便传

    # 本服务的授权验证
    API_KEY = os.getenv("API_KEY")    # 本服务允许使用的API_KEY列表
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Milvus向量数据库
    MILVUS_SERVER = 'http://127.0.0.1:19530'                                           # Milvus服务的IP地址
    MILVUS_PORT = '19530'                                                 # Milvus服务的端口号
    MILVUS_USER = 'root'                                                  # Milvus服务的用户名
    MILVUS_PASSWORD = 'cG72vdgVWX5ypaWV'                                  # Milvus服务的密码
    MILVUS_COLLECTION_NAME = "docs_collection"                             # Milvus集合名称
    MILVUS_KB_NAME = 'cursor_rag'                                         # Milvus知识库的名称
    MAX_CONTENT_LENGTH = 60000                                            # 最大内容长度

    # 知识库检索及模型
    QUESTION_REWRITE_ENABLED = True                                       # 是否开启重写重写扩展
    QUESTION_REWRITE_NUM = 3                                              # 问题重写扩展数量（额外扩展的问题数量，不含原问题）
    QUESTION_RETRIEVE_ENABLED = False                                      # 是否开启问题相关性判断
    EMBEDDING_MODEL = './model_weight/bge-m3'                            # 嵌入模型的路径
    RETRIEVE_TOPK = 5                                                     # 每个问题检索的文档数量
    RERANKING_MODEL = './model_weight/bge-reranker-v2-m3'                # 重排序模型的路径
    USE_RERANKER = True                                                   # 是否使用重排序模型进行结果优化，建议将其开启

    # 相关性判断策略
    STRATEGY = 'llm'                                                      # 相关性判断策略，可选'llm'或'thres'，选择'llm'的判断更精准一些
    THRESHOLD = 0.85   

    # Redis配置
    REDIS_HOST = "localhost"                             # Redis主机地址
    REDIS_PORT = 6379                                    # Redis端口
    REDIS_PASSWORD = "hmis1234."  # Redis密码
    REDIS_KEY = "document_disabled_key"                            # Redis键