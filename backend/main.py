import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from service.config import Config
from api import documents, rag, conversations
from service.milvus_service import MilvusService


def create_app():

    # 创建FastAPI应用
    app = FastAPI(title="CURSORCHAT")

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
    )
        
    # 挂载静态文件
    app.mount("/uploads", StaticFiles(directory=Config.UPLOAD_DIR), name="uploads")

    # 注册路由
    app.include_router(documents.router, prefix=f"{Config.API_PREFIX}{Config.API_V1_STR}/documents", tags=["documents"])
    app.include_router(rag.router, prefix=f"{Config.API_PREFIX}{Config.API_V1_STR}/rag", tags=["rag"])
    app.include_router(conversations.router, prefix=f"{Config.API_PREFIX}{Config.API_V1_STR}/conversations", tags=["conversations"])

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True) 