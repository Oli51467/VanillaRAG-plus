# 使用基础镜像
FROM python:3.12

# 设置工作目录
WORKDIR /app

# 复制requirements.txt文件
COPY backend/requirements.txt requirements.txt

# 安装依赖
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -U uvicorn fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装系统依赖
RUN apt-get clean
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

# 创建必要的目录
RUN mkdir -p /app/uploads
RUN mkdir -p /app/model_weight

# 复制除了model_weight以外的后端代码到容器中
COPY backend/api /app/api
COPY backend/db /app/db
COPY backend/milvus /app/milvus
COPY backend/scripts /app/scripts
COPY backend/service /app/service
COPY backend/utils /app/utils
COPY backend/*.py /app/
COPY backend/.env /app/

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

