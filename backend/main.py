from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional

from service.config import Config
from service.document_base import KnowledgeBase
from service.llm import LLM
from api import documents, rag, conversations


def create_app():

    # 创建FastAPI应用
    app = FastAPI(title="CURSORCHAT")

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
    )

    config = Config()
    #knowledge_base = KnowledgeBase(config)
    llm = LLM(config)

    async def verify_api_key(config: Config, authorization: Optional[str] = Header(None)):
        if not config.API_KEYS:
            logger.info("API Key 校验已跳过，因为配置中未定义任何合法 API Key。")
            return
        if not authorization:
            logger.warning("缺少 Authorization 头部")
            raise HTTPException(status_code=401, detail="Missing Authorization Header")
        if not authorization.startswith("Bearer "):
            logger.warning(f"Authorization 格式错误: {authorization}")
            raise HTTPException(status_code=402, detail="Invalid Authorization Header")
        token = authorization.split("Bearer ")[1]
        if token not in config.API_KEYS:
            logger.warning(f"非法的 API Key 尝试: {token}")
            raise HTTPException(status_code=403, detail="Invalid API Key")
        
    # 挂载静态文件
    app.mount("/uploads", StaticFiles(directory=Config.UPLOAD_DIR), name="uploads")

    # 注册路由
    app.include_router(documents.router, prefix=f"{Config.API_PREFIX}{Config.API_V1_STR}/documents", tags=["documents"])
    app.include_router(rag.router, prefix=f"{Config.API_PREFIX}{Config.API_V1_STR}/rag", tags=["rag"])
    app.include_router(conversations.router, prefix=f"{Config.API_PREFIX}{Config.API_V1_STR}/conversations", tags=["conversations"])

    return app

app = create_app()

from service.logger import logger

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 