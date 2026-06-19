"""
信任服务
管理用户信任档案和信任增长
"""
from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.trust import TrustProfile
from trust.engine import trust_engine
from config import settings


class TrustService:
    """信任服务类"""
    
    def __init__(self):
        """初始化信任服务"""
        self.max_trust = settings.MAX_TRUST_SCORE
        self.initial_trust = settings.INITIAL_TRUST_SCORE
    
    async def get_or_create_profile(
        self,
        user_id: str,
        db: AsyncSession
    ) -> TrustProfile:
        """
        获取或创建信任档案
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            信任档案
        """
        try:
            stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
            result = await db.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                # 创建新档案
                profile = TrustProfile(
                    user_id=user_id,
                    trust_score=self.initial_trust,
                    relationship_stage="stranger"
                )
                db.add(profile)
                await db.flush()
            
            return profile
        except Exception as e:
            print(f"获取信任档案失败: {e}")
            raise
    
    async def update_trust(
        self,
        user_id: str,
        message: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        分析消息并更新信任值
        
        Args:
            user_id: 用户ID
            message: 用户消息
            db: 数据库会话
            
        Returns:
            更新结果
        """
        try:
            # 获取或创建信任档案
            profile = await self.get_or_create_profile(user_id, db)
            
            # 分析消息
            analysis = await trust_engine.analyze_message(message)
            
            # 计算增长
            growth = trust_engine.calculate_trust_growth(analysis)
            
            # 更新信任值
            old_score = profile.trust_score
            new_score = min(profile.trust_score + growth, self.max_trust)
            profile.trust_score = new_score
            
            # 更新关系阶段
            old_stage = profile.relationship_stage
            profile.update_stage()
            new_stage = profile.relationship_stage
            
            return {
                "old_trust": old_score,
                "new_trust": new_score,
                "growth": growth,
                "old_stage": old_stage,
                "new_stage": new_stage,
                "analysis": analysis,
                "trust_types": trust_engine.get_trust_type_description(analysis)
            }
        except Exception as e:
            print(f"更新信任失败: {e}")
            return {
                "old_trust": 0,
                "new_trust": 0,
                "growth": 0,
                "old_stage": "stranger",
                "new_stage": "stranger",
                "analysis": {},
                "trust_types": []
            }
    
    async def get_profile(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        获取信任档案
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            信任档案信息
        """
        try:
            profile = await self.get_or_create_profile(user_id, db)
            
            return {
                "user_id": profile.user_id,
                "trust_score": profile.trust_score,
                "relationship_stage": profile.relationship_stage,
                "stage_description": self.get_stage_description(profile.relationship_stage),
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            }
        except Exception as e:
            print(f"获取信任档案失败: {e}")
            return None
    
    def get_stage_description(self, stage: str) -> str:
        """
        获取关系阶段描述
        
        Args:
            stage: 关系阶段
            
        Returns:
            阶段描述
        """
        descriptions = {
            "stranger": "刚刚认识，彼此还不太了解",
            "familiar": "已经见过几次面，对你有了初步了解",
            "friend": "我们是朋友了",
            "close_friend": "你是我的知己"
        }
        return descriptions.get(stage, "")
    
    def get_stage_progress(self, trust_score: int) -> Dict[str, Any]:
        """
        获取阶段进度
        
        Args:
            trust_score: 当前信任值
            
        Returns:
            阶段进度信息
        """
        stage_ranges = {
            "stranger": (0, 100),
            "familiar": (100, 300),
            "friend": (300, 600),
            "close_friend": (600, 1000)
        }
        
        current_stage = "stranger"
        for stage, (min_val, max_val) in stage_ranges.items():
            if min_val <= trust_score < max_val:
                current_stage = stage
                range_start, range_end = min_val, max_val
                break
        else:
            current_stage = "close_friend"
            range_start, range_end = 600, 1000
        
        progress = ((trust_score - range_start) / (range_end - range_start)) * 100
        
        # 下一个阶段
        stage_order = ["stranger", "familiar", "friend", "close_friend"]
        next_stage = None
        next_stage_score = None
        
        current_index = stage_order.index(current_stage)
        if current_index < len(stage_order) - 1:
            next_stage = stage_order[current_index + 1]
            next_stage_score = stage_ranges[next_stage][0]
        
        return {
            "current_stage": current_stage,
            "progress_percent": round(progress, 1),
            "range_start": range_start,
            "range_end": range_end,
            "next_stage": next_stage,
            "next_stage_score": next_stage_score
        }


# 全局信任服务实例
trust_service = TrustService()
