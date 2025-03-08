#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试RAG检索功能
"""

import sys
import os
import json
import numpy as np
import hashlib
from typing import List, Dict, Any

# 创建一个M3E嵌入模型模拟器类
class M3EEmbeddings:
    """模拟M3E模型的嵌入实现，适合中文文本"""
    
    def __init__(self, model_name="moka-ai/m3e-base"):
        """
        初始化M3E嵌入模型模拟器
        
        参数:
            model_name: 模型名称，仅用于记录
        """
        self.model_name = model_name
        self.dimension = 768  # m3e-base的维度
        print(f"初始化M3E模型模拟器: {model_name}")
        
        # 缓存已计算的嵌入向量，提高性能
        self._embedding_cache = {}
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量列表"""
        vectors = []
        for text in texts:
            vectors.append(self._get_cached_vector(text))
        return vectors
    
    def _get_cached_vector(self, text: str) -> List[float]:
        """从缓存中获取向量，如果不存在则计算并缓存"""
        # 使用文本的哈希值作为缓存键
        cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
        if cache_key not in self._embedding_cache:
            self._embedding_cache[cache_key] = self._text_to_vector(text)
        return self._embedding_cache[cache_key]
    
    def _text_to_vector(self, text: str) -> List[float]:
        """将文本转换为向量，使用改进的哈希方法模拟语义特征"""
        # 确保文本不为空
        if not text or len(text.strip()) == 0:
            text = "空文本"
        
        # 使用MD5哈希作为种子，这样相同的文本会产生相同的向量
        md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
        seed = int(md5, 16) % (2**32)
        np.random.seed(seed)
        
        # 生成基础向量
        base_vector = np.random.uniform(-1, 1, self.dimension).astype('float32')
        
        # 为了更好地模拟语义特征，我们对常见中文词汇和短语进行特殊处理
        # 1. 文档管理相关词汇
        doc_management_words = ["文档", "管理", "系统", "文件", "上传", "下载", "删除", "查看", "编辑", "分类", "标签", "搜索", "检索"]
        # 2. 技术相关词汇
        tech_words = ["FastAPI", "Vue", "前端", "后端", "API", "接口", "数据库", "Faiss", "向量", "嵌入", "模型", "服务器"]
        # 3. 文件类型词汇
        file_type_words = ["PDF", "TXT", "DOCX", "文本", "格式", "内容", "解析"]
        # 4. 用户交互词汇
        user_words = ["用户", "界面", "UI", "交互", "体验", "操作", "响应", "功能"]
        
        # 所有词汇分组
        word_groups = [
            (doc_management_words, 0),  # 文档管理词汇，影响向量的前1/4
            (tech_words, self.dimension // 4),  # 技术词汇，影响向量的第二个1/4
            (file_type_words, self.dimension // 2),  # 文件类型词汇，影响向量的第三个1/4
            (user_words, 3 * self.dimension // 4),  # 用户交互词汇，影响向量的最后1/4
        ]
        
        # 处理每个词汇组
        for words, offset in word_groups:
            for word in words:
                if word.lower() in text.lower():
                    # 为包含特定词汇的文本在特定维度范围内增加权重
                    word_hash = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
                    dim_index = (word_hash % (self.dimension // 4)) + offset
                    base_vector[dim_index] += 0.5
        
        # 处理常见的短语和问题
        phrases = {
            "文档管理系统": [0, 10, 20, 30],  # 影响特定的几个维度
            "如何使用": [100, 110, 120],
            "怎么上传": [200, 210, 220],
            "怎么下载": [230, 240, 250],
            "怎么删除": [260, 270, 280],
            "检索文档": [300, 310, 320],
            "搜索功能": [330, 340, 350],
            "系统功能": [400, 410, 420],
            "技术架构": [500, 510, 520],
        }
        
        for phrase, indices in phrases.items():
            if phrase in text:
                for idx in indices:
                    if idx < self.dimension:
                        base_vector[idx] += 0.8  # 短语匹配给予更高的权重
        
        # 处理问句
        if "?" in text or "？" in text or text.startswith("如何") or text.startswith("怎么") or text.startswith("请问"):
            question_indices = [50, 150, 250, 350, 450, 550, 650, 750]
            for idx in question_indices:
                if idx < self.dimension:
                    base_vector[idx] += 0.3
        
        # 归一化向量
        norm = np.linalg.norm(base_vector)
        if norm > 0:
            base_vector = base_vector / norm
            
        return base_vector.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """将查询文本转换为向量"""
        return self._get_cached_vector(text)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本之间的语义相似度"""
        # 基于向量的余弦相似度
        vec1 = self.embed_query(text1)
        vec2 = self.embed_query(text2)
        
        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        cosine_sim = dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0.0
        
        # 增强语义相似性计算
        # 1. 分词并检查共同词汇
        def tokenize(text):
            # 简单的中文分词：按字符分割，保留完整的词语
            words = []
            for word in ["文档", "系统", "管理", "上传", "下载", "删除", "查看", "搜索", "检索", 
                         "技术", "架构", "功能", "如何", "怎么", "使用", "支持", "文件", "格式"]:
                if word in text:
                    text = text.replace(word, f" {word} ")
            
            # 清理并分割
            text = text.lower().replace('？', '?').replace('，', ',').replace('。', '.')
            return [w for w in text.split() if w.strip()]
        
        words1 = set(tokenize(text1))
        words2 = set(tokenize(text2))
        common_words = words1.intersection(words2)
        
        # 计算Jaccard相似度
        jaccard_sim = len(common_words) / len(words1.union(words2)) if len(words1.union(words2)) > 0 else 0
        
        # 计算词重叠率
        word_overlap_ratio = len(common_words) / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0
        
        # 2. 检查关键词匹配
        # 关键词分组
        doc_keywords = ["文档", "文件", "内容", "格式"]
        action_keywords = ["上传", "下载", "删除", "查看", "搜索", "检索"]
        system_keywords = ["系统", "管理", "功能", "技术", "架构"]
        
        # 计算每个组的匹配度
        def calc_group_match(group):
            match = 0
            for keyword in group:
                if (keyword in text1.lower()) and (keyword in text2.lower()):
                    match += 1
            return match / len(group) if len(group) > 0 else 0
        
        doc_match = calc_group_match(doc_keywords)
        action_match = calc_group_match(action_keywords)
        system_match = calc_group_match(system_keywords)
        
        # 加权平均关键词匹配度
        keyword_match_ratio = (doc_match * 0.4 + action_match * 0.4 + system_match * 0.2)
        
        # 3. 检查问题类型匹配
        question_starters = ["如何", "怎么", "请问", "是否", "能否", "可以", "什么", "哪些"]
        
        def is_question(text):
            if "?" in text or "？" in text:
                return True
            for starter in question_starters:
                if text.startswith(starter):
                    return True
            return False
        
        is_question1 = is_question(text1)
        is_question2 = is_question(text2)
        question_type_match = 1.0 if is_question1 == is_question2 else 0.5
        
        # 4. 检查意图匹配
        intent_patterns = {
            "查询功能": ["功能", "支持", "什么", "哪些"],
            "上传操作": ["上传", "添加", "导入"],
            "下载操作": ["下载", "获取", "导出"],
            "删除操作": ["删除", "移除", "清除"],
            "技术架构": ["技术", "架构", "实现", "使用"],
            "文件格式": ["格式", "类型", "PDF", "DOCX", "TXT"]
        }
        
        def get_intent(text):
            intents = []
            for intent, patterns in intent_patterns.items():
                for pattern in patterns:
                    if pattern in text.lower():
                        intents.append(intent)
                        break
            return set(intents)
        
        intents1 = get_intent(text1)
        intents2 = get_intent(text2)
        common_intents = intents1.intersection(intents2)
        intent_match = len(common_intents) / max(len(intents1), len(intents2), 1)
        
        # 综合计算相似度，调整权重
        combined_sim = (
            cosine_sim * 0.2 +           # 向量相似度
            jaccard_sim * 0.2 +          # Jaccard词汇相似度
            word_overlap_ratio * 0.2 +   # 词重叠率
            keyword_match_ratio * 0.15 + # 关键词匹配
            question_type_match * 0.05 + # 问题类型匹配
            intent_match * 0.2           # 意图匹配
        )
        
        # 应用非线性变换，增强差异
        enhanced_sim = combined_sim ** 0.7  # 幂函数变换，增强高相似度，降低低相似度
        
        # 将相似度值映射到[0, 1]范围
        return min(max(enhanced_sim, 0.0), 1.0)

def retrieve_for_rag(query: str, model_type: int, top_k: int = 5) -> Dict[str, Any]:
    """
    检索增强生成(RAG)的检索函数
    
    参数:
        query: 用户的文本输入
        model_type: 选择的大模型类型 (1: deepseek, 2: Qwen)
        top_k: 检索的文档数量
        
    返回:
        包含检索结果和模型类型的字典
    """
    try:
        # 初始化M3E嵌入模型模拟器
        embeddings = M3EEmbeddings()
        
        # 对查询文本进行嵌入
        query_embedding = embeddings.embed_query(query)
        print(f"查询文本嵌入维度: {len(query_embedding)}")
        
        # 由于我们没有实际的向量数据库，这里模拟一些文档
        documents = [
            {"content": "这是一个基于FastAPI和Vue 3的文档管理系统，支持文档上传、查看和删除功能。", "metadata": {"source": "README.md"}},
            {"content": "系统使用Faiss向量数据库进行文档存储和检索，支持PDF、TXT、DOCX格式。", "metadata": {"source": "README.md"}},
            {"content": "前端使用Vue 3和Element Plus构建，提供友好的用户界面。", "metadata": {"source": "README.md"}},
            {"content": "后端使用FastAPI构建，提供高性能的API接口。", "metadata": {"source": "README.md"}},
            {"content": "系统支持文档向量化，自动解析文档内容并存储到Faiss向量数据库。", "metadata": {"source": "README.md"}}
        ]
        
        # 对文档内容进行嵌入
        doc_contents = [doc["content"] for doc in documents]
        doc_embeddings = embeddings.embed_documents(doc_contents)
        
        # 计算查询与文档的相似度
        retrieved_docs = []
        for i, (doc, doc_embedding) in enumerate(zip(documents, doc_embeddings)):
            # 计算向量余弦相似度
            dot_product = sum(q * d for q, d in zip(query_embedding, doc_embedding))
            query_norm = sum(q * q for q in query_embedding) ** 0.5
            doc_norm = sum(d * d for d in doc_embedding) ** 0.5
            cosine_sim = dot_product / (query_norm * doc_norm) if query_norm * doc_norm > 0 else 0
            
            # 计算语义相似度
            semantic_sim = embeddings.calculate_similarity(query, doc["content"])
            
            # 结合向量相似度和语义相似度
            combined_score = semantic_sim * 0.7 + (1.0 - cosine_sim) * 0.3
            
            retrieved_docs.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": float(combined_score)
            })
        
        # 按相似度排序
        retrieved_docs.sort(key=lambda x: x["score"], reverse=True)
        
        # 限制返回的文档数量
        top_k = min(top_k, len(retrieved_docs))
        retrieved_docs = retrieved_docs[:top_k]
        
        # 将检索到的文档内容合并为一个字符串
        context_text = "\n\n".join([doc["content"] for doc in retrieved_docs])
        
        # 确定模型类型名称
        model_name = "deepseek" if model_type == 1 else "Qwen"
        
        return {
            "query": query,
            "model_type": model_type,
            "model_name": model_name,
            "retrieved_documents": retrieved_docs,
            "context_text": context_text,
            "top_k": top_k
        }
    except Exception as e:
        print(f"RAG检索失败: {str(e)}")
        return {
            "query": query,
            "model_type": model_type,
            "error": f"检索失败: {str(e)}",
            "retrieved_documents": [],
            "context_text": "",
            "top_k": top_k
        }

def test_retrieve_for_rag():
    """测试RAG检索功能"""
    # 测试不同的查询
    queries = [
        "请介绍一下文档管理系统",
        "如何上传文档？",
        "系统支持哪些文件格式？",
        "怎么删除已上传的文档",
        "文档检索功能是如何实现的",
        "系统的技术架构是什么",
        "前端使用了什么技术",
        "后端API有哪些功能"
    ]
    
    # 选择一个模型类型进行测试
    model_type = 1  # 1: deepseek
    
    for query in queries:
        print(f"\n测试查询: {query}")
        
        # 调用retrieve_for_rag函数
        result = retrieve_for_rag(
            query=query,
            model_type=model_type,
            top_k=3
        )
        
        # 打印结果
        print(f"模型类型: {result['model_type']} ({result['model_name']})")
        print(f"检索文档数量: {len(result['retrieved_documents'])}")
        
        # 打印检索到的文档
        print("\n检索到的文档:")
        for i, doc in enumerate(result['retrieved_documents']):
            print(f"\n文档 {i+1}:")
            print(f"内容: {doc['content']}")
            print(f"分数: {doc['score']}")

def test_text_similarity():
    """测试文本相似度计算"""
    print("\n测试文本相似度计算")
    
    # 初始化M3E嵌入模型模拟器
    embeddings = M3EEmbeddings()
    
    # 测试文本对
    text_pairs = [
        ("文档管理系统支持哪些功能？", "这个系统有什么功能？"),
        ("如何上传PDF文件？", "怎么上传文档？"),
        ("系统的技术架构是什么？", "这个系统使用了什么技术？"),
        ("如何删除文档？", "怎么删除已上传的文件？"),
        ("文档管理系统支持哪些功能？", "如何使用Python编程？"),
        ("如何上传PDF文件？", "明天天气怎么样？"),
    ]
    
    # 计算并打印相似度
    for text1, text2 in text_pairs:
        similarity = embeddings.calculate_similarity(text1, text2)
        print(f"文本1: {text1}")
        print(f"文本2: {text2}")
        print(f"相似度: {similarity:.4f}")
        print()

if __name__ == "__main__":
    # 确保当前目录在Python路径中
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # 运行测试
    test_retrieve_for_rag()
    test_text_similarity() 