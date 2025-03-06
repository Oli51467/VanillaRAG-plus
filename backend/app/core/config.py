import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基本路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 上传文件存储路径
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 向量数据库路径
VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_db")
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# API配置
API_PREFIX = "/api"
API_V1_STR = "/v1"

# CORS配置
CORS_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:3000",
]

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"} 