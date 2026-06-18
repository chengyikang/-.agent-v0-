"""
情绪服务
分析和管理用户情绪
"""
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from models.emotion import EmotionLog
from emotion.analyzer import emotion_analyzer


class EmotionService:
    """情绪服务类"""
    
    def __init__(self):
        """初始化情绪服务"""
        self.emotion_categories = ["happy", "sad", "anxious", "angry", "lonely", "neutral"]
    
    async def analyze_and_log(
        self,
        user_id: str,
        message: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        分析消息情绪并记录
        
        Args:
            user_id: 用户ID
            message: 消息内容
            db: 数据库会话
            
        Returns:
            情绪分析结果
        """
        try:
            # 分析情绪
            emotion, confidence = await emotion_analyzer.analyze(message)
            
            # 记录到数据库
            emotion_log = EmotionLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                emotion=emotion,
                confidence=confidence
            )
            db.add(emotion_log)
            await db.flush()
            
            return {
                "id": emotion_log.id,
                "emotion": emotion,
                "confidence": confidence,
                "created_at": emotion_log.created_at.isoformat()
            }
        except Exception as e:
            print(f"分析情绪失败: {e}")
            return None
    
    async def get_recent_emotions(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最近的情感记录
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            limit: 限制数量
            
        Returns:
            情绪记录列表
        """
        try:
            stmt = select(EmotionLog).where(
                EmotionLog.user_id == user_id
            ).order_by(desc(EmotionLog.created_at)).limit(limit)
            
            result = await db.execute(stmt)
            emotions = result.scalars().all()
            
            return [
                {
                    "id": e.id,
                    "emotion": e.emotion,
                    "confidence": e.confidence,
                    "created_at": e.created_at.isoformat()
                }
                for e in emotions
            ]
        except Exception as e:
            print(f"获取情绪记录失败: {e}")
            return []
    
    async def get_emotion_trend(
        self,
        user_id: str,
        db: AsyncSession,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取情绪趋势
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            days: 统计天数
            
        Returns:
            每日情绪统计
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = select(
                func.date(EmotionLog.created_at).label("date"),
                EmotionLog.emotion,
                func.count(EmotionLog.id).label("count")
            ).where(
                EmotionLog.user_id == user_id,
                EmotionLog.created_at >= start_date
            ).group_by(
                func.date(EmotionLog.created_at),
                EmotionLog.emotion
            ).order_by("date")
            
            result = await db.execute(stmt)
            rows = result.all()
            
            # 转换为日期 -> 情绪分布
            trend = {}
            for row in rows:
                date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
                if date_str not in trend:
                    trend[date_str] = {"date": date_str, "total": 0}
                trend[date_str][row.emotion] = row.count
                trend[date_str]["total"] += row.count
            
            return list(trend.values())
        except Exception as e:
            print(f"获取情绪趋势失败: {e}")
            return []
    
    async def get_dominant_emotion(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> Optional[str]:
        """
        获取主导情绪
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            limit: 统计最近记录数
            
        Returns:
            主导情绪类型
        """
        try:
            stmt = select(
                EmotionLog.emotion,
                func.count(EmotionLog.id).label("count")
            ).where(
                EmotionLog.user_id == user_id
            ).group_by(
                EmotionLog.emotion
            ).order_by(desc("count")).limit(1)
            
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()
            
            return row.emotion if row else "neutral"
        except Exception as e:
            print(f"获取主导情绪失败: {e}")
            return "neutral"
    
    async def get_emotion_summary(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取情绪摘要
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            情绪摘要
        """
        try:
            # 获取最近7天的情绪统计
            trend = await self.get_emotion_trend(user_id, db, days=7)
            
            # 获取主导情绪
            dominant = await self.get_dominant_emotion(user_id, db)
            
            return {
                "dominant_emotion": dominant,
                "weekly_trend": trend,
                "needs_attention": dominant in ["sad", "anxious", "angry", "lonely"]
            }
        except Exception as e:
            print(f"获取情绪摘要失败: {e}")
            return {
                "dominant_emotion": "neutral",
                "weekly_trend": [],
                "needs_attention": False
            }


# 全局情绪服务实例
emotion_service = EmotionService()
