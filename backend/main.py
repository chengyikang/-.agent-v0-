"""
QingXi V1 主入口
FastAPI 应用入口文件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import init_db, close_db
from api import (
    user_router,
    chat_router,
    trust_router,
    memory_router,
    emotion_router,
    dashboard_router,
    analytics_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：初始化数据库
    - 关闭时：关闭数据库连接
    """
    # 启动时
    print(f"启动 {settings.APP_NAME}...")
    await init_db()
    print("数据库初始化完成")
    
    yield
    
    # 关闭时
    print("关闭应用...")
    await close_db()
    print("数据库连接已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="QingXi V1 - 慢热型陪伴 Agent 后端 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(trust_router)
app.include_router(memory_router)
app.include_router(emotion_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/api/info")
async def get_api_info():
    """获取 API 信息"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "endpoints": {
            "user": "/api/user",
            "chat": "/api/chat",
            "trust": "/api/trust",
            "memory": "/api/memory",
            "emotion": "/api/emotion",
            "dashboard": "/api/dashboard",
            "analytics": "/api/analytics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
