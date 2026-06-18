"""
情绪日志模型
存储用户情绪分析结果
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.connection import Base


class EmotionLog(Base):
    """情绪日志模型"""
    __tablename__ = "emotion_logs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    emotion: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )  # happy/sad/anxious/angry/lonely/neutral
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False
    )  # 0-1
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # 关系
    user = relationship("User", back_populates="emotion_logs")
    
    def __repr__(self) -> str:
        return f"<EmotionLog(id={self.id}, emotion={self.emotion}, confidence={self.confidence})>"
