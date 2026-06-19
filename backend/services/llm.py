"""
LLM 服务
封装多提供商 LLM API 调用（基于 OpenAI 兼容协议）
"""
import json
import logging
from typing import List, Dict, Optional, Any

from openai import AsyncOpenAI, OpenAIError

from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务类 - 支持多提供商"""
    
    def __init__(self):
        """延迟初始化，不立即创建客户端"""
        self._client: Optional[AsyncOpenAI] = None
        self._model: str = ""
        self._provider: str = ""
        self._initialized: bool = False
    
    def _ensure_init(self):
        """确保客户端已初始化（延迟到首次调用时）"""
        if self._initialized:
            return
        
        config = settings.get_llm_config()
        api_key = config["api_key"]
        base_url = config["base_url"]
        self._model = config["model"]
        self._provider = config["provider"]
        
        if not api_key:
            logger.warning(
                f"LLM API Key 未配置！请在 .env 或环境变量中设置 LLM_API_KEY。"
                f"当前提供商: {self._provider}"
            )
            self._initialized = True
            return
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None,
            timeout=60.0,
            max_retries=2,
        )
        self._initialized = True
        logger.info(f"LLM 服务已初始化 - 提供商: {self._provider}, 模型: {self._model}")
    
    @property
    def is_ready(self) -> bool:
        """检查 LLM 服务是否可用"""
        self._ensure_init()
        return self._client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        调用聊天完成接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大令牌数
            
        Returns:
            模型的回复文本
        """
        self._ensure_init()
        
        if not self._client:
            raise Exception(
                "LLM 服务未就绪，请配置 LLM_API_KEY。"
                f"当前提供商: {self._provider}，请在 .env 或 docker-compose.yml 中设置。"
            )
        
        try:
            kwargs = {
                "model": self._model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            logger.info(f"LLM 请求开始 - 模型: {self._model}, 消息数: {len(messages)}")
            response = await self._client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            logger.info(f"LLM 请求完成 - 回复长度: {len(content)}")
            return content
        except OpenAIError as e:
            logger.error(f"LLM API 调用失败 ({self._provider}): {e}")
            raise Exception(f"LLM API 调用失败 ({self._provider}): {str(e)}")
    
    async def structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用结构化输出接口
        
        Args:
            messages: 消息列表
            response_format: 结构化输出格式描述
            
        Returns:
            解析后的结构化数据
        """
        self._ensure_init()
        
        if not self._client:
            raise Exception(
                "LLM 服务未就绪，请配置 LLM_API_KEY。"
                f"当前提供商: {self._provider}"
            )
        
        try:
            kwargs = {
                "model": self._model,
                "messages": messages,
                "temperature": 0.3
            }
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self._client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or "{}"
            
            # 尝试解析 JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except (OpenAIError, json.JSONDecodeError) as e:
            raise Exception(f"结构化输出解析失败 ({self._provider}): {str(e)}")
    
    async def analysis(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        执行分析任务
        
        Args:
            prompt: 分析提示
            system_message: 系统消息
            temperature: 温度参数
            
        Returns:
            分析结果
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat_completion(messages, temperature=temperature)


# 全局 LLM 服务实例（延迟初始化，不会因密钥为空而崩溃）
llm_service = LLMService()
