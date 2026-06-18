"""
记忆 API
处理记忆查询和管理
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.connection import get_db
from services.memory import memory_service
from models.user import User

router = APIRouter(prefix="/api/memory", tags=["记忆"])


def success_response(data):
    """统一成功响应格式"""
    return {"ok": True, "data": data}


def error_response(error: str):
    """统一错误响应格式"""
    return {"ok": False, "error": error}


@router.get("")
async def get_user_memories(
    user_id: str,
    limit: int = 50,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户所有记忆
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取记忆
        memories = await memory_service.get_user_memories(
            user_id=user_id,
            db=db,
            limit=limit
        )
        
        # 按类别过滤
        if category:
            memories = [m for m in memories if m.get("category") == category]
        
        return success_response({
            "user_id": user_id,
            "memories": memories,
            "total": len(memories)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_memories(
    user_id: str,
    query: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = 5,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索相关记忆
    """
    try:
        # 检索记忆
        memories = await memory_service.retrieve_memories(
            user_id=user_id,
            query=query,
            limit=limit,
            category=category
        )
        
        return success_response({
            "query": query,
            "memories": memories,
            "total": len(memories)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_memory_categories(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取记忆类别统计
    """
    try:
        memories = await memory_service.get_user_memories(
            user_id=user_id,
            db=db,
            limit=1000
        )
        
        # 统计各类别数量
        categories = {}
        for memory in memories:
            cat = memory.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return success_response({
            "categories": categories,
            "total": len(memories)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_memories(
    user_id: str,
    conversation: str,
    db: AsyncSession = Depends(get_db)
):
    """
    从对话中提取记忆
    """
    try:
        # 检查用户是否存在
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 提取记忆
        memory_ids = await memory_service.extract_memories(
            conversation=conversation,
            user_id=user_id,
            db=db
        )
        
        return success_response({
            "extracted_count": len(memory_ids),
            "memory_ids": memory_ids
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(
    user_id: str,
    memory_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定记忆
    """
    try:
        success = await memory_service.delete_memory(
            user_id=user_id,
            memory_id=memory_id,
            db=db
        )
        
        return success_response({
            "deleted": success
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count")
async def get_memory_count(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取记忆总数
    """
    try:
        from memory.vector_store import vector_store
        
        count = vector_store.count_memories(user_id)
        
        return success_response({
            "user_id": user_id,
            "count": count
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
