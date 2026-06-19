"""
QingXi V1 配置文件
管理所有环境变量和配置项
"""
import os
from pydantic_settings import BaseSettings
from typing import List, Optional


# LLM 提供商预设配置
LLM_PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Qwen/Qwen2.5-7B-Instruct",
    },
    "custom": {
        "base_url": "",
        "default_model": "",
    },
}


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/qingxi"
    
    # LLM 提供商配置
    # 支持的提供商: openai, deepseek, moonshot, zhipu, qwen, siliconflow, custom
    LLM_PROVIDER: str = "openai"
    
    # LLM API 密钥（通用，不再叫 OPENAI_API_KEY）
    LLM_API_KEY: str = ""
    
    # 自定义 Base URL（仅 LLM_PROVIDER=custom 时需要）
    LLM_BASE_URL: str = ""
    
    # 自定义模型名（覆盖提供商默认模型）
    LLM_MODEL: str = ""
    
    # 以下保留向后兼容，优先级低于上面的通用字段
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""
    OPENAI_BASE_URL: str = ""
    
    # ChromaDB 配置
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    
    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 应用配置
    APP_NAME: str = "QingXi V1"
    DEBUG: bool = True
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 50
    MAX_MEMORY_RETRIEVAL: int = 10
    
    # 信任系统配置
    INITIAL_TRUST_SCORE: int = 10
    MAX_TRUST_SCORE: int = 1000
    
    # 人格初始值配置
    INITIAL_OPENNESS: int = 10
    INITIAL_INITIATIVE: int = 5
    INITIAL_VULNERABILITY: int = 0
    
    def get_llm_config(self) -> dict:
        """
        解析 LLM 配置，合并提供商预设和用户覆盖
        
        Returns:
            dict: {"api_key": str, "base_url": str, "model": str, "provider": str}
        """
        # 1. 确定 API Key（通用字段优先，兼容旧字段）
        api_key = self.LLM_API_KEY or self.OPENAI_API_KEY or ""
        
        # 2. 获取提供商预设
        provider = self.LLM_PROVIDER.lower()
        preset = LLM_PROVIDERS.get(provider, LLM_PROVIDERS["openai"])
        
        # 3. 确定 Base URL（自定义 > 旧字段 > 提供商预设）
        base_url = (
            self.LLM_BASE_URL 
            or self.OPENAI_BASE_URL 
            or preset["base_url"]
        )
        
        # 4. 确定模型（自定义 > 旧字段 > 提供商预设）
        model = (
            self.LLM_MODEL 
            or self.OPENAI_MODEL 
            or preset["default_model"]
        )
        
        return {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "provider": provider,
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()