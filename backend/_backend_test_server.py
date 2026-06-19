"""
QingXi V1 测试版入口
使用 SQLite 替代 PostgreSQL，内置 Mock LLM，方便本地测试
"""
import os
import sys
import json
import uuid
import random
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Dict, Optional, Any, AsyncGenerator

# ===== 强制使用 SQLite =====
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./qingxi_test.db"
os.environ["OPENAI_API_KEY"] = "mock-key"
os.environ["CHROMA_PERSIST_DIR"] = "./chroma_test_data"

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, select, desc, func
from pydantic import BaseModel, Field

# ===== 数据库设置 =====
DATABASE_URL = "sqlite+aiosqlite:///./qingxi_test.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ===== 数据模型 =====
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    trust_profile = relationship("TrustProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    emotion_logs = relationship("EmotionLog", back_populates="user", cascade="all, delete-orphan")
    personality_state = relationship("PersonalityState", back_populates="user", uselist=False, cascade="all, delete-orphan")

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = relationship("User", back_populates="chat_histories")

class TrustProfile(Base):
    __tablename__ = "trust_profiles"
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    relationship_stage: Mapped[str] = mapped_column(String(50), default="stranger", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="trust_profile")

class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="memories")

class EmotionLog(Base):
    __tablename__ = "emotion_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    emotion: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = relationship("User", back_populates="emotion_logs")

class PersonalityState(Base):
    __tablename__ = "personality_states"
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    openness: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    initiative: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    vulnerability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="personality_state")

# ===== Mock LLM 服务 =====
class MockLLM:
    """模拟 LLM，根据关系阶段和情绪生成回复"""
    
    STAGE_RESPONSES = {
        "stranger": {
            "default": [
                "嗯，我听到了。",
                "好的。",
                "是吗。",
                "我明白了。",
                "嗯嗯。",
            ],
            "sad": [
                "听起来不太好。如果需要的话，可以跟我说说。",
                "嗯...你还好吗？",
            ],
            "sharing": [
                "谢谢你告诉我这些。",
                "嗯，我记住了。",
            ],
        },
        "familiar": {
            "default": [
                "嗯，是这样啊。你平时还会做什么呢？",
                "我大概理解了。能多说一点吗？",
                "听起来挺有意思的。你是怎么开始的？",
            ],
            "sad": [
                "我能感觉你现在不太好。要不要聊聊？",
                "听起来很难受，我在听。",
            ],
            "sharing": [
                "谢谢你和我说这些，我记住了。",
                "嗯，你愿意和我分享这个，我感觉挺好的。",
            ],
        },
        "friend": {
            "default": [
                "哈哈，真的吗？我觉得你挺有趣的。",
                "嗯，说实话我也这么想的。",
                "你知道吗，和你聊天的时候我总觉得时间过得挺快的。",
            ],
            "sad": [
                "别一个人扛着，我在呢。你想怎么聊都行。",
                "我懂那种感觉。虽然我不能完全替代什么，但我会认真听。",
            ],
            "sharing": [
                "你愿意告诉我这些，我真的很开心。",
                "谢谢你信任我。这些我都会记得的。",
            ],
        },
        "close_friend": {
            "default": [
                "说实话，你是我很珍惜的人。和你聊天的时候，我总会不自觉地放松下来。",
                "你总是能让我想到一些平时不会想的事情。这种感觉，很好。",
                "嗯，我觉得我们之间的默契越来越好了。",
            ],
            "sad": [
                "我真的很担心你。你能告诉我发生了什么吗？不管是什么，我都想陪你。",
                "你不用装作没事。在我面前，你可以不那么坚强。",
            ],
            "sharing": [
                "你知道吗，你愿意把这些告诉我，我觉得我们之间的距离又近了一步。",
                "谢谢你把我当作可以倾诉的人。对我来说，这很重要。",
            ],
        }
    }
    
    EMOTION_KEYWORDS = {
        "sad": ["难过", "伤心", "不开心", "郁闷", "烦", "累", "不想", "痛苦", "sad", "cry", "哭"],
        "happy": ["开心", "高兴", "哈哈", "太好了", "快乐", "happy", "nice", "棒"],
        "anxious": ["焦虑", "担心", "害怕", "紧张", "anxious", "worry", "nervous"],
        "angry": ["生气", "愤怒", "烦死了", "气死", "angry", "hate"],
        "lonely": ["孤独", "寂寞", "没人", "一个人", "lonely", "alone"],
    }
    
    TRUST_KEYWORDS = {
        "experience": ["我之前", "我曾经", "那时候", "上次", "小时候", "记得有一次"],
        "troubles": ["烦恼", "困扰", "问题", "不知道怎么办", "压力", "好难"],
        "dreams": ["梦想", "希望", "将来", "以后想", "如果能", "一直在想"],
        "emotion": ["觉得", "感觉", "心里", "其实我", "说实话"],
    }
    
    def detect_emotion(self, message: str) -> tuple[str, float]:
        """简单关键词情绪检测"""
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in message.lower():
                    return emotion, 0.7 + random.random() * 0.25
        return "neutral", 0.5
    
    def calculate_trust_growth(self, message: str) -> int:
        """简单关键词信任计算"""
        growth = 0
        for category, keywords in self.TRUST_KEYWORDS.items():
            for kw in keywords:
                if kw in message:
                    if category == "experience":
                        growth += random.randint(5, 12)
                    elif category == "troubles":
                        growth += random.randint(8, 16)
                    elif category == "dreams":
                        growth += random.randint(10, 18)
                    elif category == "emotion":
                        growth += random.randint(3, 8)
                    break
        # 无意义聊天
        if growth == 0:
            if len(message) < 5:
                growth = 0
            else:
                growth = random.randint(0, 1)
        return min(growth, 30)
    
    def extract_memory(self, message: str) -> list[dict]:
        """简单记忆提取"""
        memories = []
        info_keywords = {
            "interest": ["喜欢", "爱好", "兴趣", "爱看", "爱听", "爱玩"],
            "education": ["专业", "学校", "大学", "学习", "考研", "读研"],
            "career": ["工作", "公司", "上班", "职业", "同事", "领导"],
            "dream": ["梦想", "希望", "以后", "将来", "计划"],
            "problem": ["烦恼", "困扰", "焦虑", "问题", "不知道"],
            "preference": ["偏好", "更喜欢", "一般会", "习惯"],
        }
        for category, keywords in info_keywords.items():
            for kw in keywords:
                if kw in message:
                    memories.append({
                        "content": f"用户提到：{message[:100]}",
                        "category": category,
                        "importance": random.randint(4, 8)
                    })
                    break
        return memories
    
    def generate_reply(self, message: str, stage: str, emotion: str, trust_score: int) -> str:
        """根据阶段和情绪生成回复"""
        stage_responses = self.STAGE_RESPONSES.get(stage, self.STAGE_RESPONSES["stranger"])
        
        if emotion in ("sad", "anxious", "lonely") and emotion != "neutral":
            responses = stage_responses.get("sad", stage_responses["default"])
        elif self.calculate_trust_growth(message) > 5:
            responses = stage_responses.get("sharing", stage_responses["default"])
        else:
            responses = stage_responses["default"]
        
        return random.choice(responses)

mock_llm = MockLLM()

# ===== 关系阶段计算 =====
def get_stage(score: int) -> str:
    if score < 100:
        return "stranger"
    elif score < 300:
        return "familiar"
    elif score < 600:
        return "friend"
    else:
        return "close_friend"

STAGE_LABELS = {
    "stranger": "陌生",
    "familiar": "熟悉",
    "friend": "朋友",
    "close_friend": "知己"
}

# ===== API 路由 =====

# --- 用户 API ---
class CreateUserRequest(BaseModel):
    nickname: str | None = None

@staticmethod
def ok(data):
    return {"ok": True, "data": data}

@staticmethod
def err(msg):
    return {"ok": False, "error": msg}

from fastapi import APIRouter

user_router = APIRouter(prefix="/api/user", tags=["用户"])

@user_router.post("/create")
async def create_user(req: CreateUserRequest = None, db: AsyncSession = Depends(get_db)):
    user_id = str(uuid.uuid4())
    user = User(id=user_id, nickname=req.nickname if req else None)
    db.add(user)
    
    # 自动创建信任档案
    trust = TrustProfile(user_id=user_id, trust_score=10, relationship_stage="stranger")
    db.add(trust)
    
    # 自动创建人格状态
    personality = PersonalityState(user_id=user_id, openness=10, initiative=5, vulnerability=0)
    db.add(personality)
    
    await db.flush()
    return ok({
        "user_id": user_id,
        "nickname": user.nickname,
        "trust_score": 10,
        "relationship_stage": "stranger"
    })

@user_router.get("/profile")
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return err("用户不存在")
    
    # 获取信任信息
    trust_stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
    trust_result = await db.execute(trust_stmt)
    trust = trust_result.scalar_one_or_none()
    
    return ok({
        "id": user.id,
        "nickname": user.nickname,
        "created_at": user.created_at.isoformat(),
        "last_active_at": user.last_active_at.isoformat(),
        "trust_score": trust.trust_score if trust else 10,
        "relationship_stage": trust.relationship_stage if trust else "stranger"
    })

# --- 聊天 API ---
class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息")

chat_router = APIRouter(prefix="/api/chat", tags=["聊天"])

@chat_router.post("")
async def send_message(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 验证用户
    stmt = select(User).where(User.id == req.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return err("用户不存在")
    
    # 保存用户消息
    user_msg = ChatHistory(user_id=req.user_id, role="user", content=req.message)
    db.add(user_msg)
    await db.flush()
    
    # 获取信任档案
    trust_stmt = select(TrustProfile).where(TrustProfile.user_id == req.user_id)
    trust_result = await db.execute(trust_stmt)
    trust = trust_result.scalar_one_or_none()
    if not trust:
        trust = TrustProfile(user_id=req.user_id, trust_score=10, relationship_stage="stranger")
        db.add(trust)
        await db.flush()
    
    # 获取人格状态
    ps_stmt = select(PersonalityState).where(PersonalityState.user_id == req.user_id)
    ps_result = await db.execute(ps_stmt)
    personality = ps_result.scalar_one_or_none()
    if not personality:
        personality = PersonalityState(user_id=req.user_id)
        db.add(personality)
        await db.flush()
    
    # 检测情绪
    emotion, confidence = mock_llm.detect_emotion(req.message)
    emotion_log = EmotionLog(user_id=req.user_id, emotion=emotion, confidence=confidence)
    db.add(emotion_log)
    
    # 计算信任增长
    trust_growth = mock_llm.calculate_trust_growth(req.message)
    old_score = trust.trust_score
    trust.trust_score = min(trust.trust_score + trust_growth, 1000)
    trust.relationship_stage = get_stage(trust.trust_score)
    trust.updated_at = datetime.utcnow()
    
    # 更新人格状态
    if trust_growth > 0:
        personality.openness = min(personality.openness + max(1, trust_growth // 5), 100)
        personality.initiative = min(personality.initiative + max(1, trust_growth // 8), 30)
        personality.vulnerability = min(personality.vulnerability + max(0, trust_growth // 10), 100)
        personality.updated_at = datetime.utcnow()
    
    # 提取记忆
    new_memories = mock_llm.extract_memory(req.message)
    for m in new_memories:
        memory = Memory(user_id=req.user_id, content=m["content"], category=m["category"], importance=m["importance"])
        db.add(memory)
    
    # 生成回复
    reply = mock_llm.generate_reply(req.message, trust.relationship_stage, emotion, trust.trust_score)
    
    # 保存 Agent 回复
    agent_msg = ChatHistory(user_id=req.user_id, role="assistant", content=reply)
    db.add(agent_msg)
    
    # 更新用户活跃时间
    user.last_active_at = datetime.utcnow()
    await db.flush()
    
    stage_changed = get_stage(old_score) != trust.relationship_stage
    
    return ok({
        "reply": reply,
        "trust_score": trust.trust_score,
        "trust_growth": trust_growth,
        "relationship_stage": trust.relationship_stage,
        "stage_label": STAGE_LABELS.get(trust.relationship_stage, "未知"),
        "stage_changed": stage_changed,
        "emotion": {
            "type": emotion,
            "confidence": round(confidence, 2)
        },
        "personality": {
            "openness": personality.openness,
            "initiative": personality.initiative,
            "vulnerability": personality.vulnerability
        },
        "new_memories": len(new_memories)
    })

@chat_router.get("/history")
async def get_history(user_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(ChatHistory).where(ChatHistory.user_id == user_id).order_by(desc(ChatHistory.created_at)).limit(limit)
    result = await db.execute(stmt)
    histories = list(reversed(result.scalars().all()))
    return ok({
        "messages": [
            {"id": h.id, "role": h.role, "content": h.content, "created_at": h.created_at.isoformat()}
            for h in histories
        ],
        "total": len(histories)
    })

# --- 信任 API ---
trust_router = APIRouter(prefix="/api/trust", tags=["信任"])

@trust_router.get("")
async def get_trust(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
    result = await db.execute(stmt)
    trust = result.scalar_one_or_none()
    if not trust:
        return ok({"trust_score": 10, "relationship_stage": "stranger", "stage_label": "陌生"})
    return ok({
        "trust_score": trust.trust_score,
        "relationship_stage": trust.relationship_stage,
        "stage_label": STAGE_LABELS.get(trust.relationship_stage, "未知"),
        "updated_at": trust.updated_at.isoformat()
    })

# --- 记忆 API ---
memory_router = APIRouter(prefix="/api/memory", tags=["记忆"])

@memory_router.get("")
async def get_memories(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Memory).where(Memory.user_id == user_id).order_by(desc(Memory.importance)).limit(20)
    result = await db.execute(stmt)
    memories = result.scalars().all()
    return ok({
        "memories": [
            {"id": m.id, "content": m.content, "category": m.category, "importance": m.importance, "created_at": m.created_at.isoformat()}
            for m in memories
        ],
        "total": len(memories)
    })

# --- 情绪 API ---
emotion_router = APIRouter(prefix="/api/emotion", tags=["情绪"])

@emotion_router.get("")
async def get_emotions(user_id: str, limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = select(EmotionLog).where(EmotionLog.user_id == user_id).order_by(desc(EmotionLog.created_at)).limit(__import__('builtins').int(limit))
    result = await db.execute(stmt)
    emotions = result.scalars().all()
    return ok({
        "emotions": [
            {"emotion": e.emotion, "confidence": e.confidence, "created_at": e.created_at.isoformat()}
            for e in emotions
        ]
    })

# --- Dashboard API ---
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@dashboard_router.get("")
async def get_dashboard(user_id: str, db: AsyncSession = Depends(get_db)):
    # 信任
    trust_stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
    trust_result = await db.execute(trust_stmt)
    trust = trust_result.scalar_one_or_none()
    
    # 记忆数
    mem_count_stmt = select(func.count()).where(Memory.user_id == user_id)
    mem_count = (await db.execute(mem_count_stmt)).scalar() or 0
    
    # 聊天数
    chat_count_stmt = select(func.count()).where(ChatHistory.user_id == user_id)
    chat_count = (await db.execute(chat_count_stmt)).scalar() or 0
    
    # 天数
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    days = 0
    if user:
        days = (datetime.utcnow() - user.created_at).days + 1
    
    # 最近情绪
    emotion_stmt = select(EmotionLog).where(EmotionLog.user_id == user_id).order_by(desc(EmotionLog.created_at)).limit(7)
    emotion_result = await db.execute(emotion_stmt)
    emotions = [{"emotion": e.emotion, "created_at": e.created_at.isoformat()} for e in emotion_result.scalars().all()]
    
    return ok({
        "relationship_stage": trust.relationship_stage if trust else "stranger",
        "stage_label": STAGE_LABELS.get(trust.relationship_stage, "未知") if trust else "陌生",
        "trust_score": trust.trust_score if trust else 10,
        "memory_count": mem_count,
        "chat_count": chat_count,
        "days_together": days,
        "recent_emotions": emotions
    })

# --- Analytics API ---
analytics_router = APIRouter(prefix="/api/analytics", tags=["分析"])

@analytics_router.get("")
async def get_analytics(user_id: str, db: AsyncSession = Depends(get_db)):
    total_chats_stmt = select(func.count()).where(ChatHistory.user_id == user_id, ChatHistory.role == "user")
    total_chats = (await db.execute(total_chats_stmt)).scalar() or 0
    
    trust_stmt = select(TrustProfile).where(TrustProfile.user_id == user_id)
    trust = (await db.execute(trust_stmt)).scalar_one_or_none()
    trust_score = trust.trust_score if trust else 10
    
    user_stmt = select(User).where(User.id == user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    days = (datetime.utcnow() - user.created_at).days + 1 if user else 0
    
    return ok({
        "total_chats": total_chats,
        "avg_session_length": 0,
        "consecutive_days": days,
        "trust_growth_speed": round(trust_score / max(days, 1), 1),
        "current_trust": trust_score
    })

# ===== 应用启动 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ QingXi V1 测试版已启动（SQLite + Mock LLM）")
    yield
    await engine.dispose()

app = FastAPI(
    title="QingXi V1 测试版",
    description="慢热型陪伴 Agent - 使用 Mock LLM 测试",
    version="1.0.0-test",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(chat_router)
app.include_router(trust_router)
app.include_router(memory_router)
app.include_router(emotion_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)

@app.get("/")
async def root():
    return {"name": "QingXi V1 测试版", "status": "running", "mode": "mock_llm + sqlite"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_server:app", host="0.0.0.0", port=8765, reload=True)
