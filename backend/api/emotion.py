"""
情绪 API
处理情绪分析结果查询
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.connection import get_db
from services.emotion import emotion_service
from models.user import User

router = APIRouter(prefix="/api/emotion", tags=["情绪"])


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.get("")
async def get_emotion_logs(
    user_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近的情感记录
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取情绪记录
        emotions = await emotion_service.get_recent_emotions(
            user_id=user_id,
            db=db,
            limit=limit
        )
        
        return success_response({
            "user_id": user_id,
            "emotions": emotions,
            "total": len(emotions)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend")
async def get_emotion_trend(
    user_id: str,
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取情绪趋势
    """
    try:
        trend = await emotion_service.get_emotion_trend(
            user_id=user_id,
            db=db,
            days=days
        )
        
        return success_response({
            "user_id": user_id,
            "days": days,
            "trend": trend
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dominant")
async def get_dominant_emotion(
    user_id: str,
    limit: int = Query(20, ge=5, le=100, description="统计记录数"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取主导情绪
    """
    try:
        dominant = await emotion_service.get_dominant_emotion(
            user_id=user_id,
            db=db,
            limit=limit
        )
        
        emotion_descriptions = {
            "happy": "快乐",
            "sad": "悲伤",
            "anxious": "焦虑",
            "angry": "愤怒",
            "lonely": "孤独",
            "neutral": "中性"
        }
        
        return success_response({
            "user_id": user_id,
            "dominant_emotion": dominant,
            "description": emotion_descriptions.get(dominant, "未知")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_emotion_summary(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取情绪摘要
    """
    try:
        summary = await emotion_service.get_emotion_summary(
            user_id=user_id,
            db=db
        )
        
        return success_response({
            "user_id": user_id,
            **summary
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_emotion(
    user_id: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """
    分析消息情绪
    """
    try:
        result = await emotion_service.analyze_and_log(
            user_id=user_id,
            message=message,
            db=db
        )
        
        if not result:
            return error_response("情绪分析失败")
        
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
