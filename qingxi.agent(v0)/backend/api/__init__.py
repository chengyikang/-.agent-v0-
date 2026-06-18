"""
API 模块
定义所有 API 路由
"""
from api.user import router as user_router
from api.chat import router as chat_router
from api.trust import router as trust_router
from api.memory import router as memory_router
from api.emotion import router as emotion_router
from api.dashboard import router as dashboard_router
from api.analytics import router as analytics_router

__all__ = [
    "user_router",
    "chat_router",
    "trust_router",
    "memory_router",
    "emotion_router",
    "dashboard_router",
    "analytics_router"
]
