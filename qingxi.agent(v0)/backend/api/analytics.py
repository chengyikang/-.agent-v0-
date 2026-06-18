"""
Analytics API
提供数据分析功能
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from database.connection import get_db
from models.user import User
from models.chat import ChatHistory
from models.trust import TrustProfile

router = APIRouter(prefix="/api/analytics", tags=["数据分析"])


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.get("")
async def get_analytics(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户数据分析
    
    返回：
    - total_chats: 总对话轮次
    - avg_session_length: 平均会话长度
    - consecutive_days: 连续活跃天数
    - trust_growth_speed: 信任增长速度
    - avg_session_duration: 平均会话时长
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 统计总对话数
        chat_count_stmt = select(func.count(ChatHistory.id)).where(
            ChatHistory.user_id == user_id
        )
        chat_result = await db.execute(chat_count_stmt)
        total_chats = chat_result.scalar() or 0
        
        # 统计用户消息数
        user_msg_stmt = select(func.count(ChatHistory.id)).where(
            ChatHistory.user_id == user_id,
            ChatHistory.role == "user"
        )
        user_result = await db.execute(user_msg_stmt)
        user_message_count = user_result.scalar() or 0
        
        # 计算平均会话长度（每轮对话的来回次数）
        avg_session_length = round(user_message_count / max(1, (total_chats - user_message_count)), 1)
        
        # 计算连续活跃天数
        consecutive_days = await calculate_consecutive_days(user_id, db)
        
        # 获取信任档案
        trust_stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
        trust_result = await db.execute(trust_stmt)
        trust_profile = trust_result.scalar_one_or_none()
        
        # 计算信任增长速度（每天）
        if trust_profile:
            days_since_creation = (datetime.utcnow() - trust_profile.created_at).days + 1
            trust_growth_speed = round(trust_profile.trust_score / days_since_creation, 2) if days_since_creation > 0 else 0
        else:
            trust_growth_speed = 0
        
        # 计算平均会话时长（简化版，基于消息时间戳）
        avg_session_duration = await calculate_avg_session_duration(user_id, db)
        
        return success_response({
            "user_id": user_id,
            "total_chats": total_chats,
            "user_message_count": user_message_count,
            "avg_session_length": avg_session_length,
            "consecutive_days": consecutive_days,
            "trust_growth_speed": trust_growth_speed,
            "avg_session_duration_minutes": avg_session_duration,
            "created_at": user.created_at.isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def calculate_consecutive_days(user_id: str, db: AsyncSession) -> int:
    """
    计算连续活跃天数
    """
    try:
        # 获取最近的消息，按日期分组
        stmt = select(
            func.date(ChatHistory.created_at).label("date")
        ).where(
            ChatHistory.user_id == user_id
        ).distinct().order_by(desc("date")).limit(30)
        
        result = await db.execute(stmt)
        dates = [row.date for row in result.all()]
        
        if not dates:
            return 0
        
        consecutive_days = 0
        today = datetime.utcnow().date()
        
        for i, date in enumerate(dates):
            date_obj = date if hasattr(date, 'year') else datetime.strptime(str(date), "%Y-%m-%d").date()
            expected_date = today - timedelta(days=i)
            
            if date_obj == expected_date:
                consecutive_days += 1
            else:
                break
        
        return consecutive_days
    except Exception:
        return 0


async def calculate_avg_session_duration(user_id: str, db: AsyncSession) -> float:
    """
    计算平均会话时长（分钟）
    """
    try:
        # 获取最近的消息时间戳
        stmt = select(ChatHistory.created_at).where(
            ChatHistory.user_id == user_id
        ).order_by(desc(ChatHistory.created_at)).limit(10)
        
        result = await db.execute(stmt)
        timestamps = [row.created_at for row in result.all()]
        
        if len(timestamps) < 2:
            return 0
        
        # 计算相邻消息的时间差
        total_duration = 0
        count = 0
        
        for i in range(len(timestamps) - 1):
            duration = (timestamps[i] - timestamps[i + 1]).total_seconds() / 60
            if duration < 60:  # 忽略超过1小时的时间间隔（可能是离开）
                total_duration += duration
                count += 1
        
        return round(total_duration / count, 1) if count > 0 else 0
    except Exception:
        return 0


@router.get("/engagement")
async def get_engagement_stats(
    user_id: str,
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户参与度统计
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 统计期间消息数
        stmt = select(func.count(ChatHistory.id)).where(
            ChatHistory.user_id == user_id,
            ChatHistory.created_at >= start_date
        )
        result = await db.execute(stmt)
        message_count = result.scalar() or 0
        
        # 统计活跃天数
        active_days_stmt = select(
            func.date(ChatHistory.created_at)
        ).where(
            ChatHistory.user_id == user_id,
            ChatHistory.created_at >= start_date
        ).distinct().count()
        
        active_result = await db.execute(active_days_stmt)
        active_days = active_result.scalar() or 0
        
        return success_response({
            "user_id": user_id,
            "period_days": days,
            "message_count": message_count,
            "active_days": active_days,
            "avg_messages_per_day": round(message_count / days, 1),
            "engagement_rate": round(active_days / days * 100, 1)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trust-history")
async def get_trust_history(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取信任历史（基于关系阶段变化）
    """
    try:
        trust_stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
        trust_result = await db.execute(trust_stmt)
        trust_profile = trust_result.scalar_one_or_none()
        
        if not trust_profile:
            return success_response({
                "history": [],
                "current_score": 10
            })
        
        # 模拟历史数据
        current_score = trust_profile.trust_score
        stage = trust_profile.relationship_stage
        
        history = []
        stages = ["stranger", "familiar", "friend", "close_friend"]
        stage_thresholds = [100, 300, 600]
        
        for i, threshold in enumerate(stage_thresholds):
            if current_score >= threshold:
                history.append({
                    "stage": stages[i + 1],
                    "achieved": True
                })
            else:
                history.append({
                    "stage": stages[i + 1],
                    "achieved": False,
                    "remaining": threshold - current_score
                })
        
        return success_response({
            "current_score": current_score,
            "current_stage": stage,
            "history": history
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-patterns")
async def get_chat_patterns(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取聊天模式分析
    """
    try:
        # 获取最近消息
        stmt = select(ChatHistory).where(
            ChatHistory.user_id == user_id
        ).order_by(desc(ChatHistory.created_at)).limit(100)
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        if not messages:
            return success_response({
                "avg_message_length": 0,
                "peak_hours": [],
                "total_words": 0
            })
        
        # 计算平均消息长度
        user_messages = [m for m in messages if m.role == "user"]
        total_words = sum(len(m.content) for m in user_messages)
        avg_length = round(total_words / len(user_messages), 1) if user_messages else 0
        
        # 分析活跃时段
        from collections import Counter
        hours = [m.created_at.hour for m in user_messages]
        hour_counts = Counter(hours)
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return success_response({
            "avg_message_length": avg_length,
            "total_words": total_words,
            "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
            "total_conversations": len(user_messages)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
