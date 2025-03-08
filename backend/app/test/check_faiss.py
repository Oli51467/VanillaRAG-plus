import faiss
import numpy as np
import os
from pathlib import Path

# 基本路径
BASE_DIR = Path(__file__).resolve().parent
VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_db")

def check_faiss():
    """检查Faiss是否正确安装和配置"""
    print("检查Faiss是否正确安装...")
    
    # 检查Faiss版本
    print(f"Faiss版本: {faiss.__version__}")
    
    # 创建一个简单的索引
    dimension = 128
    index = faiss.IndexFlatL2(dimension)
    
    # 生成一些随机向量
    nb = 100
    vectors = np.random.random((nb, dimension)).astype('float32')
    
    # 添加向量到索引
    index.add(vectors)
    
    # 检查索引是否正常工作
    print(f"索引中的向量数量: {index.ntotal}")
    
    # 执行一次简单的搜索
    k = 5
    query = np.random.random((1, dimension)).astype('float32')
    distances, indices = index.search(query, k)
    
    print(f"搜索结果 - 距离: {distances[0][:5]}")
    print(f"搜索结果 - 索引: {indices[0][:5]}")
    
    # 检查向量数据库目录
    if os.path.exists(VECTOR_DB_PATH):
        print(f"向量数据库目录存在: {VECTOR_DB_PATH}")
        files = os.listdir(VECTOR_DB_PATH)
        if files:
            print(f"向量数据库目录中的文件: {files}")
        else:
            print("向量数据库目录为空")
    else:
        print(f"向量数据库目录不存在: {VECTOR_DB_PATH}")
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        print(f"已创建向量数据库目录: {VECTOR_DB_PATH}")
    
    print("Faiss检查完成！")

if __name__ == "__main__":
    check_faiss() 