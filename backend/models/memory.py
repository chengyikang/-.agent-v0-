"""
记忆模型
存储用户的重要信息和偏好
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.connection import Base


class Memory(Base):
    """记忆模型"""
    __tablename__ = "memories"
    
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
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # interest/education/career/dream/problem/preference/important_event
    importance: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False
    )  # 1-10
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    user = relationship("User", back_populates="memories")
    
    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, category={self.category}, importance={self.importance})>"
