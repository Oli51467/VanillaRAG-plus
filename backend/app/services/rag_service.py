import os
from typing import List, Dict, Any, Tuple

from app.services import get_document_service
from app.services.model_service import ModelService
from langchain.schema.document import Document


class RAGService:
    """检索增强生成服务"""
    
    def __init__(self):
        """初始化服务"""
        self.document_service = get_document_service()
        self.model_service = ModelService()
    
    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """
        根据用户输入检索相关文档
        
        Args:
            query: 用户输入文本
            top_k: 返回的相关文档数量
            
        Returns:
            包含文档和相似度分数的列表
        """
        try:
            # 使用向量数据库检索相关文档
            docs_with_scores = self.document_service.search_documents(query, top_k)
            return docs_with_scores
        except Exception as e:
            print(f"检索相关文档失败: {str(e)}")
            return []
    
    def format_context_for_llm(self, docs_with_scores: List[Tuple[Document, float]]) -> str:
        """
        将检索到的文档格式化为大模型可用的上下文
        
        Args:
            docs_with_scores: 检索到的文档和相似度分数列表
            
        Returns:
            格式化后的上下文文本
        """
        context = ""
        
        for i, (doc, score) in enumerate(docs_with_scores):
            # 格式化文档内容
            context += f"内容: {doc.page_content}\n"
        
        return context
    
    def generate_rag_prompt(self, query: str, top_k: int = 5) -> Tuple[str, int]:
        """
        生成RAG的完整提示
        
        Args:
            query: 用户输入文本
            top_k: 返回的相关文档数量
            
        Returns:
            格式化后的提示文本，可以直接发送给大模型
        """
        # 获取相关文档
        docs_with_scores = self.retrieve_relevant_documents(query, top_k)
        
        # 如果没有找到相关文档
        if not docs_with_scores:
            return f"用户问题: {query}\n\n没有找到相关文档，请根据您的知识来回答这个问题。"
        
        # 格式化上下文
        context = self.format_context_for_llm(docs_with_scores)
        
        # 构建提示
        prompt_template = f"""请回答下面的问题。请使用以下提供的文档内容来帮助回答，如果文档内容不足以回答问题，请使用您自己的知识。相关文档:{context}用户问题: {query}。请根据以上信息提供详细回答:"""
            
        return prompt_template, len(docs_with_scores)
    

    def get_rag_response(self, query: str, model: str = "Qwen/QwQ-32B", top_k: int = 5) -> Dict[str, Any]:
        """
        获取RAG完整响应
        
        Args:
            query: 用户输入文本
            model: 模型名称
            top_k: 返回的相关文档数量
            
        Returns:
            包含提示和回复的字典
        """
        # 生成提示
        prompt, documents_count = self.generate_rag_prompt(query, top_k)
        
        # 调用大模型
        response = self.model_service.call_model(prompt=prompt, model=model)
        
        return {
            "prompt": prompt,
            "response": response,
            "documents_count": documents_count
        } 