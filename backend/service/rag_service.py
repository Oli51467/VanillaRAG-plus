from typing import List, Dict, Any, Tuple
import json
import asyncio

from service.document_service import DocumentService
from service.conversation_service import ConversationService
from sqlalchemy.orm import Session
from service.llm_service import LLM_Service
from service.prompts import build_rewrite_prompt
from service.logger import logger
from service.config import Config

class RAGService:
    def __init__(self, db: Session):
        self.document_service = DocumentService(db)
        self.conversation_service = ConversationService(db)
        self.model_service = LLM_Service(Config)

    async def non_streaming_workflow(self, conversation_id: str, user_query: str, model: str = "Qwen/QwQ-32B", top_k: int = 5) -> Dict[str, Any]:
        # Step 1: 获取该对话的所有历史消息和最后一条消息
        history_messages = self.conversation_service.get_conversation_messages(conversation_id)
        # 截掉最后一条
        if len(history_messages) > 0:
            history_messages = history_messages[:-1]
        logger.info("获取历史消息完成...")

        # Step 2: 对原问题进行重新扩展
        expanded_questions = await self.rewrite_question(self.model_service, user_query, Config.QUESTION_REWRITE_NUM)
        if len(history_messages) > 0:
            expanded_questions.append(history_messages[-1].content)
        logger.info("重写扩展完成...")
    
        # Step 3: 判断是否需要检索知识库
        if Config.QUESTION_RETRIEVE_ENABLED:
            logger.info("判断是否需要检索知识库...")

        # Step 4: 检索知识库
        logger.info("检索知识库...")
        search_tasks = [self.document_service.search_documents(question, Config.RETRIEVE_TOPK) for question in expanded_questions]
        #search_results = await asyncio.gather(*search_tasks)
        logger.info("检索知识库完成...")

        # Step 5: 调用大模型
        # Step 6: 返回结果

        # # 生成提示
        # prompt, documents_count = self.generate_rag_prompt(query, top_k)
        
        # # 调用大模型
        # response = self.model_service.async_chat_completion(prompt)
        
        return {
            'prompt': expanded_questions[0],
            'response': expanded_questions[0],
            'documents_count': 1
        } 
    
    async def rewrite_question(self, llm_service: LLM_Service, original_question: str, question_rewrite_num: int) -> List:
        """
        使用 LLM 将用户的原始问题进行扩展，返回新的问题列表。
        根据 question_rewrite_num 生成对应数量的重写问法。
        如果 JSON 解析失败或内容不符合预期，会进行3次重试，全部重试失败则只返回原问题。
        """
        rewrite_prompt = build_rewrite_prompt(original_question, question_rewrite_num)
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"重写问题第{attempt + 1}次尝试重写扩展...")
            rewrite_response = await llm_service.await_chat_completion(rewrite_prompt, "你是一个问题扩展助手，可以帮我对原问题进行扩展。")

            try:
                expansions = json.loads(rewrite_response)
                if not isinstance(expansions, list) or len(expansions) == 0:
                    raise ValueError("解析结果不是有效的列表")
                
                questions = [item['question'] for item in expansions if 'question' in item]
                print(questions)
                if len(questions) < question_rewrite_num:
                    raise ValueError("重写问题数不足。")

                return questions
            
            except Exception as e:
                logger.warning(f"重写扩展解析失败 (第 {attempt} 次): {e}")
                if attempt < max_retries:
                    asyncio.sleep(0.02)
                else:
                    logger.warning("已达最大重试次数，放弃重写扩展。")
        
        return [original_question]