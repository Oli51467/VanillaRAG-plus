from typing import List, Dict, Any, Tuple
import json
import time
import asyncio
import uuid

from service.document_service import DocumentService
from service.conversation_service import ConversationService
from sqlalchemy.orm import Session
from service.llm_service import LLM_Service
from service.prompts import build_rewrite_prompt
from service.logger import logger
from service.config import Config
import service.prompts as prompts
class RAGService:
    def __init__(self, db: Session):
        self.document_service = DocumentService(db)
        self.conversation_service = ConversationService(db)
        self.llm_service = LLM_Service(Config)

    async def non_streaming_workflow(self, conversation_id: str, user_query: str, model: str = "Qwen/QwQ-32B", top_k: int = 5) -> Dict[str, Any]:
        needs_retrieve_chunk = True
        request_id = str(uuid.uuid4())

        # Step 1: 获取该对话的所有历史消息和最后一条消息
        history_messages = self.conversation_service.get_conversation_messages(conversation_id)
        last_message_content = history_messages[-1].content
        formatted_history_messages = [{"role": message.role, "content": message.content} for message in history_messages]
        logger.info("获取历史消息完成...")

        # Step 2: 对原问题进行重新扩展
        expanded_questions = await self.rewrite_question(self.llm_service, user_query, Config.QUESTION_REWRITE_NUM)
        if len(history_messages) > 0:
            expanded_questions.append(last_message_content)
        logger.info("重写扩展完成...")
    
        # Step 3: 判断是否需要检索知识库
        if Config.QUESTION_RETRIEVE_ENABLED:
            logger.info("判断是否需要检索知识库...")
            judgements = []
            for expanded_question in expanded_questions:
                is_relevant = await self.chat_judge_relevant(self.llm_service, last_message_content, formatted_history_messages[:-1])
                judgements.append(is_relevant)
            relevant_count = sum(1 for j in judgements if j)
            needs_retrieve_chunk = relevant_count >= len(expanded_questions) / 2
            if not needs_retrieve_chunk:
                logger.info(f'不需要检索知识库，大模型直接生成...')
            
        # Step 4: 检索知识库
        if needs_retrieve_chunk:
            logger.info("检索知识库...")
            search_tasks = [self.document_service.retrieve(question, Config.RETRIEVE_TOPK) for question in expanded_questions]
            task_results = await asyncio.gather(*search_tasks)
            print(f"检索知识库结果: {task_results}")
            retrieved_chunks = []
            for (chunks, references) in task_results:
                retrieved_chunks.extend(chunks)
            # 去重
            #retrieved_chunks = self.deduplicate_chunks(retrieved_chunks) 
            logger.info(f'检索出的文档切片: {retrieved_chunks}')
            logger.info(f'检索出的相关文档数量: {len(retrieved_chunks)}')
            logger.info("开始数据相关性分析...")

            # Step 5: 数据相关性分析
            tasks = [
                self.chunk_judge_relevant(self.llm_service, last_message_content, chunk, formatted_history_messages)
                for chunk in retrieved_chunks
            ]
            relevancy_results = await asyncio.gather(*tasks)
            hit_chunks = [chunk for chunk, is_rel in zip(retrieved_chunks, relevancy_results) if is_rel][:Config.RETRIEVE_TOPK]
            doc_names = [chunk['doc_name'] for chunk in hit_chunks if chunk['doc_name']]
            references = list(dict.fromkeys(doc_names))
            logger.info(f'相关性判断后的文档切片: {hit_chunks}')
            logger.info(f'相关性判断后的相关文档数量: {len(hit_chunks)}')
            logger.info(f'相关性判断后的相关文档名称: {references}')    

        # Step 6: 调用大模型
        if needs_retrieve_chunk and 'hit_chunks' in locals() and hit_chunks:
            instruction, response = await self.decorate_answer(request_id, self.llm_service, hit_chunks, formatted_history_messages)
        else:
            instruction, response = await self.decorate_answer(request_id, self.llm_service, [], formatted_history_messages)
        
        logger.info(f'final response: {response}')
        return {
            'prompt': instruction,
            'response': response,
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
            rewrite_response = await llm_service.async_chat_completion([
                {"role": "system", "content": "你是一个问题扩展助手，可以帮我对原问题进行扩展。"},
                {"role": "user", "content": rewrite_prompt}
            ])

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
    
    def deduplicate_chunks(self, chunks):
        """
        去重切片，切片的text相同则视为是一个，只保留每组中得分最高的切片。
        """
        retrieved_chunks_map = {}

        for chunk in chunks:
            chunk_copy = chunk.copy()
            score_value = chunk_copy.pop('score', None)

            chunk_key = frozenset(chunk_copy.items())

            if chunk_key not in retrieved_chunks_map:
                retrieved_chunks_map[chunk_key] = {
                    'score': score_value,
                    **chunk_copy
                }
            else:
                existing_score = retrieved_chunks_map[chunk_key]['score']
                if score_value > existing_score:
                    retrieved_chunks_map[chunk_key] = {
                        'score': score_value,
                        **chunk_copy
                    }

        deduplicated_chunks = []
        for chunk_key, chunk_data in retrieved_chunks_map.items():
            restored_chunk = {
                'score': chunk_data['score'],
                **dict(chunk_key)
            }
            deduplicated_chunks.append(restored_chunk)

        return deduplicated_chunks
    
    async def chunk_judge_relevant(self, llm_service: LLM_Service, query, chunk, history=[]):
        '''
        判断切片的文本是否与用户的问题相关
        '''
        prompt = prompts.RELEVANT_PROMPT_TEMPLATE.format(chunk_text=chunk['text'][:500], query=query)
        response = await llm_service.async_chat_completion(
            [*history, {"role": "user", "content": prompt}],
            temperature=0, extra_body={"type": ["否", "是"]}
        )
        return response.strip() == "是"
    
    async def chat_judge_relevant(self, llm_service: LLM_Service, query, history=[]):
        prompt = prompts.CHAT_PROMPT_TEMPLATE.format(query=query)
        response = await llm_service.async_chat_completion(
            [*history, {"role": "user", "content": prompt}],
            temperature=0, extra_body={"type": ["否", "是"]}
        )
        return response.strip() == "是"
    
    async def decorate_answer(self, request_id, llm_service: LLM_Service, chunks, messages):
        '''
        将从知识库中检索到的chunks放入最终回答指令, 生成答案。
        '''
        kb_text = "\n\n".join(chunk["text"] for chunk in chunks)
        instruction = prompts.ANSWER_PROMPT_TEMPLATE.format(
            current_date=time.strftime("%Y年%m月%d日", time.localtime()),
            kb_text=kb_text
        )
        response = await llm_service.async_chat_completion(
            [{"role": "system", "content": instruction}, *messages],
        )
        return instruction, response