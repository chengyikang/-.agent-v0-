"""
人格服务
管理人格状态和成长
"""
from typing import Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.personality import PersonalityState
from personality.engine import personality_engine
from config import settings


class PersonalityService:
    """人格服务类"""
    
    def __init__(self):
        """初始化人格服务"""
        self.initial_values = {
            "openness": settings.INITIAL_OPENNESS,
            "initiative": settings.INITIAL_INITIATIVE,
            "vulnerability": settings.INITIAL_VULNERABILITY
        }
    
    async def get_or_create_state(
        self,
        user_id: str,
        db: AsyncSession
    ) -> PersonalityState:
        """
        获取或创建人格状态
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            人格状态
        """
        try:
            stmt = select(PersonalityState).where(PersonalityState.user_id == user_id)
            result = await db.execute(stmt)
            state = result.scalar_one_or_none()
            
            if not state:
                # 创建新状态
                state = PersonalityState(
                    user_id=user_id,
                    openness=self.initial_values["openness"],
                    initiative=self.initial_values["initiative"],
                    vulnerability=self.initial_values["vulnerability"]
                )
                db.add(state)
                await db.flush()
            
            return state
        except Exception as e:
            print(f"获取人格状态失败: {e}")
            raise
    
    async def update_from_trust_growth(
        self,
        user_id: str,
        trust_growth: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        根据信任增长更新人格状态
        
        Args:
            user_id: 用户ID
            trust_growth: 信任增长值
            db: 数据库会话
            
        Returns:
            更新结果
        """
        try:
            # 获取当前状态
            state = await self.get_or_create_state(user_id, db)
            
            current = {
                "openness": state.openness,
                "initiative": state.initiative,
                "vulnerability": state.vulnerability
            }
            
            # 计算增长
            growth = personality_engine.calculate_growth(trust_growth)
            
            # 应用增长
            new_state = personality_engine.apply_growth(current, growth)
            
            # 更新数据库
            state.openness = new_state["openness"]
            state.initiative = new_state["initiative"]
            state.vulnerability = new_state["vulnerability"]
            
            return {
                "old_state": current,
                "growth": growth,
                "new_state": new_state,
                "description": personality_engine.get_personality_description(new_state),
                "guidance": personality_engine.get_response_guidance(new_state)
            }
        except Exception as e:
            print(f"更新人格状态失败: {e}")
            return {
                "old_state": self.initial_values,
                "growth": {},
                "new_state": self.initial_values,
                "description": "",
                "guidance": {}
            }
    
    async def get_state(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        获取人格状态
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            人格状态信息
        """
        try:
            state = await self.get_or_create_state(user_id, db)
            
            current = {
                "openness": state.openness,
                "initiative": state.initiative,
                "vulnerability": state.vulnerability
            }
            
            return {
                "user_id": state.user_id,
                "openness": state.openness,
                "initiative": state.initiative,
                "vulnerability": state.vulnerability,
                "description": personality_engine.get_personality_description(current),
                "guidance": personality_engine.get_response_guidance(current),
                "openness_description": state.get_openness_description(),
                "initiative_description": state.get_initiative_description(),
                "vulnerability_description": state.get_vulnerability_description(),
                "created_at": state.created_at.isoformat(),
                "updated_at": state.updated_at.isoformat()
            }
        except Exception as e:
            print(f"获取人格状态失败: {e}")
            return None


# 全局人格服务实例
personality_service = PersonalityService()
