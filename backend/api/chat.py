"""
聊天 API
处理消息发送和聊天历史获取
"""
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from services.chat import chat_service
from models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/api/chat", tags=["聊天"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    user_message_id: str
    assistant_message_id: str
    response: str
    emotion: dict
    trust_update: dict
    personality_update: dict
    new_memories: list
    context: dict


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.post("")
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息并获取回复
    
    完整流程：
    1. 保存用户消息
    2. 获取信任档案和人格状态
    3. 检索相关记忆
    4. 分析情绪
    5. 构建 Prompt
    6. 调用 LLM 获取回复
    7. 保存 Agent 回复
    8. 更新信任值
    9. 更新人格状态
    10. 提取并保存新记忆
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == request.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 处理消息
        result = await chat_service.process_message(
            user_id=request.user_id,
            message=request.message,
            db=db
        )
        
        if "error" in result:
            return error_response(result["error"])
        
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    获取聊天历史
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取历史
        histories = await chat_service.get_history_dict(
            user_id=user_id,
            db=db,
            limit=limit
        )
        
        return success_response({
            "user_id": user_id,
            "histories": histories,
            "total": len(histories)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_messages(
    user_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近消息（简化版）
    """
    try:
        histories = await chat_service.get_history_dict(
            user_id=user_id,
            db=db,
            limit=limit
        )
        
        return success_response({
            "messages": histories
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
