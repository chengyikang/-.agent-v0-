"""
信任 API
处理信任档案查询和管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.connection import get_db
from services.trust import trust_service
from models.user import User

router = APIRouter(prefix="/api/trust", tags=["信任"])


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.get("")
async def get_trust_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户信任档案
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取信任档案
        profile = await trust_service.get_profile(user_id, db)
        
        if not profile:
            raise HTTPException(status_code=404, detail="信任档案不存在")
        
        # 获取阶段进度
        progress = trust_service.get_stage_progress(profile["trust_score"])
        
        return success_response({
            **profile,
            "progress": progress
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stage")
async def get_relationship_stage(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取关系阶段
    """
    try:
        profile = await trust_service.get_profile(user_id, db)
        
        if not profile:
            return success_response({
                "stage": "stranger",
                "description": "刚刚认识，彼此还不太了解"
            })
        
        return success_response({
            "stage": profile["relationship_stage"],
            "description": profile["stage_description"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress")
async def get_trust_progress(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取信任值进度
    """
    try:
        profile = await trust_service.get_profile(user_id, db)
        
        if not profile:
            return success_response({
                "current_stage": "stranger",
                "progress_percent": 0,
                "next_stage": "familiar",
                "next_stage_score": 100
            })
        
        progress = trust_service.get_stage_progress(profile["trust_score"])
        
        return success_response(progress)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_message_trust(
    user_id: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """
    分析单条消息的信任表达
    """
    try:
        from trust.engine import trust_engine
        
        # 分析消息
        analysis = await trust_engine.analyze_message(message)
        growth = trust_engine.calculate_trust_growth(analysis)
        types = trust_engine.get_trust_type_description(analysis)
        
        return success_response({
            "analysis": analysis,
            "potential_growth": growth,
            "trust_types": types
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
