import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取配置
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", 8080))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=host, port=port, reload=True) 