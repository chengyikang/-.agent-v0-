"""
记忆服务
提取和检索长期记忆
"""
import uuid
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models.memory import Memory
from memory.vector_store import vector_store


MEMORY_EXTRACTION_PROMPT = """你是一个记忆提取专家。请从对话中提取用户的重要信息，保存为长期记忆。

对话内容:
{conversation}

请返回一个JSON格式的记忆列表，每个记忆包含以下字段:
- content: 记忆内容（简洁，30字以内）
- category: 记忆类别，必须是以下之一:
  - interest: 兴趣爱好
  - education: 教育背景
  - career: 职业工作
  - dream: 梦想愿望
  - problem: 烦恼问题
  - preference: 偏好习惯
  - important_event: 重要事件
- importance: 重要性（1-10），表示这条信息对未来对话的重要程度

如果没有提取到重要记忆，返回空数组 []。

只返回JSON数组，不要有其他文字。

示例:
[
  {{"content": "用户喜欢跑步", "category": "interest", "importance": 7}},
  {{"content": "用户正在找工作", "category": "career", "importance": 8}}
]"""


class MemoryService:
    """记忆服务类"""
    
    def __init__(self):
        """初始化记忆服务"""
        self.max_memories_per_extraction = 5  # 每次最多提取5条记忆
    
    async def extract_memories(
        self,
        conversation: str,
        user_id: str,
        db: AsyncSession
    ) -> List[str]:
        """
        从对话中提取记忆
        
        Args:
            conversation: 对话内容
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            提取的记忆ID列表
        """
        from services.llm import llm_service
        
        try:
            # 调用 LLM 提取记忆
            prompt = MEMORY_EXTRACTION_PROMPT.format(conversation=conversation)
            result = await llm_service.analysis(
                prompt=prompt,
                system_message="你是一个记忆提取专家，只返回JSON格式的记忆列表。"
            )
            
            # 解析结果
            if isinstance(result, str):
                import json
                result = json.loads(result)
            
            if not result or not isinstance(result, list):
                return []
            
            # 保存记忆
            memory_ids = []
            for memory_data in result[:self.max_memories_per_extraction]:
                memory_id = await self.create_memory(
                    user_id=user_id,
                    content=memory_data.get("content", ""),
                    category=memory_data.get("category", "important_event"),
                    importance=memory_data.get("importance", 5),
                    db=db
                )
                if memory_id:
                    memory_ids.append(memory_id)
            
            return memory_ids
        except Exception as e:
            print(f"提取记忆失败: {e}")
            return []
    
    async def create_memory(
        self,
        user_id: str,
        content: str,
        category: str,
        importance: int,
        db: AsyncSession
    ) -> Optional[str]:
        """
        创建记忆
        
        Args:
            user_id: 用户ID
            content: 记忆内容
            category: 记忆类别
            importance: 重要性
            db: 数据库会话
            
        Returns:
            记忆ID
        """
        try:
            memory_id = str(uuid.uuid4())
            
            # 保存到数据库
            memory = Memory(
                id=memory_id,
                user_id=user_id,
                content=content,
                category=category,
                importance=min(max(importance, 1), 10)
            )
            db.add(memory)
            await db.flush()
            
            # 保存到向量存储
            vector_store.add_memory(
                user_id=user_id,
                memory_id=memory_id,
                content=content,
                category=category,
                importance=importance
            )
            
            return memory_id
        except Exception as e:
            print(f"创建记忆失败: {e}")
            return None
    
    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            limit: 返回数量
            category: 可选的类别过滤
            
        Returns:
            记忆列表
        """
        return vector_store.search_memories(
            user_id=user_id,
            query=query,
            n_results=limit,
            category=category
        )
    
    async def get_user_memories(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户所有记忆
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            limit: 限制数量
            
        Returns:
            记忆列表
        """
        try:
            stmt = select(Memory).where(
                Memory.user_id == user_id
            ).order_by(desc(Memory.importance), desc(Memory.created_at)).limit(limit)
            
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "category": m.category,
                    "importance": m.importance,
                    "created_at": m.created_at.isoformat()
                }
                for m in memories
            ]
        except Exception as e:
            print(f"获取记忆失败: {e}")
            return []
    
    async def delete_memory(
        self,
        user_id: str,
        memory_id: str,
        db: AsyncSession
    ) -> bool:
        """
        删除记忆
        
        Args:
            user_id: 用户ID
            memory_id: 记忆ID
            db: 数据库会话
            
        Returns:
            是否成功
        """
        try:
            # 从数据库删除
            stmt = select(Memory).where(
                Memory.id == memory_id,
                Memory.user_id == user_id
            )
            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()
            
            if memory:
                await db.delete(memory)
            
            # 从向量存储删除
            vector_store.delete_memory(user_id, memory_id)
            
            return True
        except Exception as e:
            print(f"删除记忆失败: {e}")
            return False
    
    def get_memory_context(
        self,
        memories: List[Dict[str, Any]]
    ) -> str:
        """
        将记忆列表转换为上下文文本
        
        Args:
            memories: 记忆列表
            
        Returns:
            上下文文本
        """
        if not memories:
            return ""
        
        context_parts = ["关于用户的重要信息："]
        for i, memory in enumerate(memories, 1):
            category_names = {
                "interest": "兴趣",
                "education": "教育",
                "career": "职业",
                "dream": "梦想",
                "problem": "烦恼",
                "preference": "偏好",
                "important_event": "重要事件"
            }
            category = category_names.get(memory.get("category", ""), memory.get("category", ""))
            context_parts.append(f"{i}. [{category}]{memory.get('content', '')}")
        
        return "\n".join(context_parts)


# 全局记忆服务实例
memory_service = MemoryService()
