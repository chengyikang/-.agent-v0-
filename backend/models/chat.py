"""
聊天历史模型
存储用户与 QingXi 的对话记录
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.connection import Base


class ChatHistory(Base):
    """聊天历史模型"""
    __tablename__ = "chat_histories"
    
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
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" 或 "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # 关系
    user = relationship("User", back_populates="chat_histories")
    
    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, role={self.role}, user_id={self.user_id})>"
