# 服务初始化文件 
from .document_service import DocumentService

# 单例实例
_document_service_instance = None

def get_document_service():
    """
    返回DocumentService的单例实例
    """
    global _document_service_instance
    if _document_service_instance is None:
        _document_service_instance = DocumentService()
    return _document_service_instance

# 导入其他服务
from .rag_service import RAGService 