import os
import requests
from typing import Dict, Any, List, Optional

class ModelService:
    """大模型调用服务"""
    
    def __init__(self):
        """初始化服务"""
        # 从配置文件获取API密钥
        self.api_key = os.getenv("API_KEY")
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        
    def call_model(self, prompt: str, model: str = "Qwen/QwQ-32B", max_tokens: int = 512, 
                  temperature: float = 0.7, top_p: float = 0.7, 
                  top_k: int = 50, frequency_penalty: float = 0.5) -> str:
        """
        调用大模型API
        
        Args:
            prompt: 提示文本
            model: 模型名称
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top-p参数
            top_k: top-k参数
            frequency_penalty: 频率惩罚参数
            
        Returns:
            模型生成的回复文本
        """
        try:
            # 构建API请求
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "max_tokens": max_tokens,
                "stop": None,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "frequency_penalty": frequency_penalty,
                "n": 1,
                "response_format": {"type": "text"},
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "description": "",
                            "name": "",
                            "parameters": {},
                            "strict": False
                        }
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 检查是否有API密钥
            if not self.api_key:
                return "错误：未配置Deepseek API密钥，请在环境变量中设置DEEPSEEK_API_KEY"
            
            # 发送请求
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                # 提取回复内容
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "API返回了空的回复"
            else:
                return f"API调用失败: HTTP {response.status_code}, {response.text}"
                
        except Exception as e:
            return f"调用模型时出错: {str(e)}" 