"""
用户模型
存储用户基本信息
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.connection import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    trust_profile = relationship("TrustProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    emotion_logs = relationship("EmotionLog", back_populates="user", cascade="all, delete-orphan")
    personality_state = relationship("PersonalityState", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname})>"
