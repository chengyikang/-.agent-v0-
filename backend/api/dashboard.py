"""
Dashboard API
提供用户仪表盘数据
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.connection import get_db
from services.trust import trust_service
from services.emotion import emotion_service
from services.memory import memory_service
from models.user import User
from models.chat import ChatHistory

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.get("")
async def get_dashboard(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户仪表盘数据
    
    返回：
    - relationship_stage: 关系阶段
    - trust_score: 信任值
    - memory_count: 记忆数量
    - days_together: 相处的天数
    - emotion_trend: 最近7天情绪趋势
    - trust_growth_curve: 信任增长曲线
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取信任档案
        trust_profile = await trust_service.get_profile(user_id, db)
        
        # 获取记忆数量
        from memory.vector_store import vector_store
        memory_count = vector_store.count_memories(user_id)
        
        # 计算相处天数
        created_at = user.created_at
        days_together = (datetime.utcnow() - created_at).days + 1
        
        # 获取情绪趋势
        emotion_trend = await emotion_service.get_emotion_trend(
            user_id=user_id,
            db=db,
            days=7
        )
        
        # 获取聊天统计
        chat_stmt = select(func.count(ChatHistory.id)).where(
            ChatHistory.user_id == user_id
        )
        chat_result = await db.execute(chat_stmt)
        total_chats = chat_result.scalar() or 0
        
        # 获取最近活跃时间
        recent_stmt = select(func.max(ChatHistory.created_at)).where(
            ChatHistory.user_id == user_id
        )
        recent_result = await db.execute(recent_stmt)
        last_chat_time = recent_result.scalar()
        
        # 获取情绪摘要
        emotion_summary = await emotion_service.get_emotion_summary(user_id, db)
        
        # 构建信任增长曲线（简化版，基于当前值估算）
        trust_growth_curve = []
        if trust_profile:
            current_score = trust_profile["trust_score"]
            # 估算增长
            for i in range(7):
                day_score = max(10, current_score - (6 - i) * 2)  # 简化估算
                trust_growth_curve.append({
                    "day": i,
                    "score": int(day_score)
                })
        
        return success_response({
            "user_id": user_id,
            "nickname": user.nickname,
            "relationship_stage": trust_profile["relationship_stage"] if trust_profile else "stranger",
            "trust_score": trust_profile["trust_score"] if trust_profile else 10,
            "trust_max": 1000,
            "stage_description": trust_profile["stage_description"] if trust_profile else "",
            "memory_count": memory_count,
            "days_together": days_together,
            "total_chats": total_chats,
            "emotion_trend": emotion_trend,
            "emotion_summary": emotion_summary,
            "trust_growth_curve": trust_growth_curve,
            "created_at": user.created_at.isoformat(),
            "last_active_at": user.last_active_at.isoformat(),
            "last_chat_at": last_chat_time.isoformat() if last_chat_time else None
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_overview(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取概览数据（简化版）
    """
    try:
        # 获取信任档案
        trust_profile = await trust_service.get_profile(user_id, db)
        
        # 获取记忆数量
        from memory.vector_store import vector_store
        memory_count = vector_store.count_memories(user_id)
        
        # 获取情绪摘要
        emotion_summary = await emotion_service.get_emotion_summary(user_id, db)
        
        return success_response({
            "relationship_stage": trust_profile["relationship_stage"] if trust_profile else "stranger",
            "trust_score": trust_profile["trust_score"] if trust_profile else 10,
            "memory_count": memory_count,
            "needs_attention": emotion_summary.get("needs_attention", False)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取统计数据
    """
    try:
        # 获取用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 统计聊天数
        chat_count_stmt = select(func.count(ChatHistory.id)).where(
            ChatHistory.user_id == user_id
        )
        chat_result = await db.execute(chat_count_stmt)
        total_messages = chat_result.scalar() or 0
        
        # 统计用户消息数
        user_msg_stmt = select(func.count(ChatHistory.id)).where(
            ChatHistory.user_id == user_id,
            ChatHistory.role == "user"
        )
        user_result = await db.execute(user_msg_stmt)
        user_messages = user_result.scalar() or 0
        
        # 计算相处天数
        days_together = (datetime.utcnow() - user.created_at).days + 1
        
        return success_response({
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": total_messages - user_messages,
            "days_together": days_together,
            "avg_messages_per_day": round(total_messages / days_together, 1) if days_together > 0 else 0
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
