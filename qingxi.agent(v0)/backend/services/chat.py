"""
聊天服务
核心聊天逻辑：调用 prompt builder、调用 LLM、保存历史
"""
import uuid
import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models.chat import ChatHistory
from models.trust import TrustProfile
from models.personality import PersonalityState
from services.llm import llm_service
from services.trust import trust_service
from services.memory import memory_service
from services.emotion import emotion_service
from services.personality import personality_service
from prompt.builder import prompt_builder
from emotion.analyzer import emotion_analyzer

logger = logging.getLogger(__name__)


def is_invalid_response(text: str) -> bool:
    """检查回复是否无效（省略号、过短、无实际内容）"""
    if not text or not text.strip():
        return True
    stripped = text.strip()
    # 纯省略号
    if re.match(r'^[.。…·\s]+$', stripped):
        return True
    # 过短（少于5个有效字符）
    meaningful = re.sub(r'[.。…·,，!！?？\s、～~—－\-]+', '', stripped)
    if len(meaningful) < 5:
        return True
    return False


class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        self.history_limit = 50
        self.memory_retrieval_limit = 5
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        处理用户消息，返回 Agent 回复
        """
        try:
            # 1. 保存用户消息
            user_chat = ChatHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                role="user",
                content=message
            )
            db.add(user_chat)
            await db.flush()
            logger.info(f"用户消息已保存 - user_id: {user_id}")
            
            # 2. 获取信任档案
            trust_profile = await trust_service.get_or_create_profile(user_id, db)
            relationship_stage = trust_profile.relationship_stage
            trust_score = trust_profile.trust_score
            
            # 3. 获取人格状态
            personality_state = await personality_service.get_or_create_state(user_id, db)
            personality_dict = {
                "openness": personality_state.openness,
                "initiative": personality_state.initiative,
                "vulnerability": personality_state.vulnerability
            }
            
            # 4. 分析情绪（规则引擎，无LLM）
            emotion_result = await emotion_service.analyze_and_log(user_id, message, db)
            emotion_hint = ""
            if emotion_result and emotion_result["confidence"] > 0.6:
                emotion_hint = emotion_analyzer.get_emotion_response_hint(emotion_result["emotion"])
            logger.info(f"情绪分析完成 - emotion: {emotion_result}")
            
            # 5. 检索相关记忆（加超时保护）
            memory_context = ""
            try:
                memories = await asyncio.wait_for(
                    memory_service.retrieve_memories(
                        user_id=user_id,
                        query=message,
                        limit=self.memory_retrieval_limit
                    ),
                    timeout=5.0
                )
                memory_context = memory_service.get_memory_context(memories)
                logger.info(f"记忆检索完成 - 记忆数: {len(memories) if memories else 0}")
            except asyncio.TimeoutError:
                logger.warning("记忆检索超时（5秒），跳过记忆上下文")
            except Exception as e:
                logger.warning(f"记忆检索失败（不影响主回复）: {e}")
            
            # 6. 获取最近对话历史
            recent_history = await self.get_recent_history(user_id, db, limit=20)
            history_dicts = [
                {"role": h.role, "content": h.content}
                for h in recent_history
            ]
            
            # 7. 构建 Prompt 并调用 LLM
            messages = prompt_builder.build_chat_prompt(
                user_message=message,
                relationship_stage=relationship_stage,
                trust_score=trust_score,
                personality_state=personality_dict,
                memory_context=memory_context,
                emotion_hint=emotion_hint,
                recent_history=history_dicts
            )
            
            logger.info(f"LLM 请求开始 - 模型: {llm_service._model}, 消息数: {len(messages)}")
            response = await llm_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            logger.info(f"LLM 第一次回复 - 长度: {len(response)}, 内容: {response[:100]}")
            
            # 8. 后处理校验：如果回复无效，重试一次（加强提示）
            if is_invalid_response(response):
                logger.warning(f"LLM 回复无效（省略号/过短），自动重试 - 原回复: [{response}]")
                retry_messages = messages + [
                    {"role": "assistant", "content": response},
                    {"role": "user", "content": "请用至少两句话回复我，不要只发省略号或沉默，认真回答好吗？"}
                ]
                response = await llm_service.chat_completion(
                    messages=retry_messages,
                    temperature=0.9,
                    max_tokens=500
                )
                logger.info(f"LLM 重试回复 - 长度: {len(response)}, 内容: {response[:100]}")
                
                # 如果重试还是无效，给一个兜底回复
                if is_invalid_response(response):
                    logger.warning(f"LLM 重试仍无效，使用兜底回复")
                    response = self._get_fallback_response(message, relationship_stage)
            
            # 9. 保存 Agent 回复
            assistant_chat = ChatHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                role="assistant",
                content=response
            )
            db.add(assistant_chat)
            
            # 更新用户最后活跃时间
            from models.user import User
            user_stmt = select(User).where(User.id == user_id)
            user_result = await db.execute(user_stmt)
            user_obj = user_result.scalar_one_or_none()
            if user_obj:
                user_obj.last_active_at = datetime.utcnow()
            
            # 先提交消息
            await db.commit()
            
            # ===== 后台处理，不阻塞主回复 =====
            trust_update = {"growth": 1, "old_trust": trust_score, "new_trust": trust_score}
            personality_update = {}
            new_memory_ids = []
            
            try:
                trust_update = await trust_service.update_trust(user_id, message, db)
                personality_update = await personality_service.update_from_trust_growth(
                    user_id,
                    trust_update.get("growth", 0),
                    db
                )
                await db.commit()
            except Exception as e:
                logger.warning(f"后台更新信任/人格失败（不影响主回复）: {e}")
            
            # 定期提取记忆
            if len(history_dicts) % 5 == 0 and len(history_dicts) > 0:
                try:
                    conversation_text = "\n".join([
                        f'{"用户" if h["role"] == "user" else "清溪"}：{h["content"]}'
                        for h in history_dicts[-10:]
                    ])
                    conversation_text += f'\n用户：{message}\n清溪：{response}'
                    new_memory_ids = await memory_service.extract_memories(
                        conversation=conversation_text,
                        user_id=user_id,
                        db=db
                    )
                    await db.commit()
                except Exception as e:
                    logger.warning(f"后台提取记忆失败（不影响主回复）: {e}")
            
            return {
                "user_message_id": user_chat.id,
                "assistant_message_id": assistant_chat.id,
                "response": response,
                "emotion": emotion_result,
                "trust_update": trust_update,
                "personality_update": personality_update,
                "new_memories": new_memory_ids,
                "context": {
                    "relationship_stage": relationship_stage,
                    "trust_score": trust_score,
                    "personality": personality_dict
                }
            }
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "response": "抱歉，我现在有些问题，无法回复你。"
            }
    
    def _get_fallback_response(self, message: str, stage: str) -> str:
        """兜底回复：当LLM持续返回无效内容时使用"""
        fallbacks = {
            "stranger": "嗯，我在听。你说的我记下了，能再告诉我多一些吗？",
            "familiar": "我在呢，你说的我都听到了。想继续聊聊吗？",
            "friend": "我一直在认真听你说呢。还有什么想跟我分享的吗？",
            "close_friend": "你说的话我都放在心上了。跟我说说，你现在的感受怎么样？"
        }
        return fallbacks.get(stage, fallbacks["stranger"])
    
    async def get_recent_history(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 50
    ) -> List[ChatHistory]:
        """获取最近聊天历史"""
        try:
            stmt = select(ChatHistory).where(
                ChatHistory.user_id == user_id
            ).order_by(desc(ChatHistory.created_at)).limit(limit)
            result = await db.execute(stmt)
            histories = result.scalars().all()
            return list(reversed(histories))
        except Exception as e:
            logger.error(f"获取聊天历史失败: {e}")
            return []
    
    async def get_history_dict(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取聊天历史（字典格式）"""
        histories = await self.get_recent_history(user_id, db, limit)
        return [
            {
                "id": h.id,
                "role": h.role,
                "content": h.content,
                "created_at": h.created_at.isoformat()
            }
            for h in histories
        ]


# 全局聊天服务实例
chat_service = ChatService()
