"""
用户 API
处理用户创建和基本信息获取
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database.connection import get_db
from models.user import User
from models.trust import TrustProfile
from models.personality import PersonalityState

router = APIRouter(prefix="/api/user", tags=["用户"])


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.post("/create")
async def create_user(
    nickname: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户
    自动生成 UUID 并初始化相关档案
    """
    try:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # 创建用户
        user = User(
            id=user_id,
            nickname=nickname,
            created_at=now,
            last_active_at=now
        )
        db.add(user)
        
        # 创建信任档案
        trust_profile = TrustProfile(
            user_id=user_id,
            trust_score=10,  # 初始信任值
            relationship_stage="stranger",
            created_at=now
        )
        db.add(trust_profile)
        
        # 创建人格状态
        personality_state = PersonalityState(
            user_id=user_id,
            openness=10,
            initiative=5,
            vulnerability=0,
            created_at=now
        )
        db.add(personality_state)
        
        await db.commit()
        
        return success_response({
            "user_id": user_id,
            "nickname": nickname,
            "created_at": now.isoformat()
        })
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户信息
    """
    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return success_response({
            "user_id": user.id,
            "nickname": user.nickname,
            "created_at": user.created_at.isoformat(),
            "last_active_at": user.last_active_at.isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/nickname")
async def update_nickname(
    user_id: str,
    nickname: str,
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户昵称
    """
    try:
        stmt = update(User).where(User.id == user_id).values(nickname=nickname)
        await db.execute(stmt)
        await db.commit()
        
        return success_response({
            "user_id": user_id,
            "nickname": nickname
        })
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-activity")
async def update_activity(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户最后活跃时间
    """
    try:
        stmt = update(User).where(User.id == user_id).values(
            last_active_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        return success_response({"updated": True})
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
