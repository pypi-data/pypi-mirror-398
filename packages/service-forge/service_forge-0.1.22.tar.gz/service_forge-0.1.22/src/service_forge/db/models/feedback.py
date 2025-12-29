from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class FeedbackBase(Base):
    """反馈数据表模型"""
    __tablename__ = "feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), nullable=False, index=True)
    workflow_name = Column(String(255), nullable=False, index=True)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=True, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典格式"""
        return {
            "feedback_id": str(self.feedback_id),
            "task_id": self.task_id,
            "workflow_name": self.workflow_name,
            "rating": self.rating,
            "comment": self.comment,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at,
        }
