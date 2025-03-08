from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import API_PREFIX, API_V1_STR, CORS_ORIGINS, UPLOAD_DIR
from app.api import documents, search, rag

# 创建FastAPI应用
app = FastAPI(title="文档管理系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(documents.router, prefix=f"{API_PREFIX}{API_V1_STR}/documents", tags=["documents"])
app.include_router(search.router, prefix=f"{API_PREFIX}{API_V1_STR}/search", tags=["search"])
app.include_router(rag.router, prefix=f"{API_PREFIX}{API_V1_STR}/rag", tags=["rag"])

@app.get("/")
async def root():
    return {"message": "文档管理系统API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 