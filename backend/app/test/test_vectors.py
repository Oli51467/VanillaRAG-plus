import os
import sys
from pathlib import Path
import numpy as np
import faiss
import pickle

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent))

# 导入我们的自定义类
from app.services.document_service import SimpleEmbeddings, DocumentService

def verify_vector_db():
    """验证向量数据库中的内容"""
    print("开始验证向量数据库...")
    
    # 获取向量数据库路径
    vector_db_path = os.path.join(Path(__file__).resolve().parent, "vector_db")
    
    # 检查文件是否存在
    index_faiss_path = os.path.join(vector_db_path, "index.faiss")
    index_pkl_path = os.path.join(vector_db_path, "index.pkl")
    
    if not os.path.exists(index_faiss_path) or not os.path.exists(index_pkl_path):
        print(f"错误: 向量数据库文件不存在")
        return False
    
    print(f"向量数据库文件存在:")
    print(f"- {index_faiss_path} ({os.path.getsize(index_faiss_path) / 1024:.2f} KB)")
    print(f"- {index_pkl_path} ({os.path.getsize(index_pkl_path) / 1024:.2f} KB)")
    
    try:
        # 加载pickle文件，获取文档内容和元数据
        with open(index_pkl_path, 'rb') as f:
            pkl_data = pickle.load(f)
            
        # 检查pickle文件内容
        if 'docstore' in pkl_data:
            docstore = pkl_data['docstore']
            if hasattr(docstore, '_dict'):
                docs = docstore._dict
                print(f"\n向量数据库中的文档数量: {len(docs)}")
                
                # 显示文档内容摘要
                print("\n文档内容摘要:")
                for i, (doc_id, doc) in enumerate(docs.items()):
                    if i >= 5:  # 只显示前5个文档
                        print(f"... 还有 {len(docs) - 5} 个文档")
                        break
                    
                    content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    print(f"文档 {i+1}:")
                    print(f"  ID: {doc_id}")
                    print(f"  内容: {content_preview}")
                    print(f"  元数据: {doc.metadata}")
                    print()
        
        # 加载FAISS索引，验证向量
        index = faiss.read_index(index_faiss_path)
        print(f"\nFAISS索引信息:")
        print(f"向量维度: {index.d}")
        print(f"向量数量: {index.ntotal}")
        
        # 如果有向量，尝试进行一次简单的搜索
        if index.ntotal > 0:
            # 创建一个简单的嵌入模型
            embeddings = SimpleEmbeddings(dimension=index.d)
            
            # 生成一个查询向量
            query_text = "测试查询"
            query_vector = np.array([embeddings.embed_query(query_text)]).astype('float32')
            
            # 执行搜索
            k = min(5, index.ntotal)  # 最多返回5个结果
            distances, indices = index.search(query_vector, k)
            
            print(f"\n执行测试查询 '{query_text}':")
            print(f"搜索结果 - 距离: {distances[0]}")
            print(f"搜索结果 - 索引: {indices[0]}")
            
            # 尝试获取搜索结果对应的文档
            if 'docstore' in pkl_data:
                docstore = pkl_data['docstore']
                if hasattr(docstore, '_dict'):
                    docs = list(docstore._dict.values())
                    print("\n搜索结果对应的文档:")
                    for i, idx in enumerate(indices[0]):
                        if idx < len(docs):
                            doc = docs[idx]
                            content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                            print(f"结果 {i+1} (距离: {distances[0][i]:.4f}):")
                            print(f"  内容: {content_preview}")
                            print()
        
        return True
    except Exception as e:
        print(f"验证过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 创建文档服务实例，加载向量数据库
    doc_service = DocumentService()
    
    # 获取所有文档
    documents = doc_service.get_all_documents()
    print(f"文档管理系统中的文档数量: {len(documents)}")
    
    # 显示文档列表
    if documents:
        print("\n文档列表:")
        for i, doc in enumerate(documents):
            print(f"{i+1}. {doc['file_name']} (ID: {doc['id']})")
    
    # 验证向量数据库
    verify_vector_db() 