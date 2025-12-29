from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class TagBase(Base):
    __tablename__ = "tag"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    type = Column(String(50), nullable=True)
    user_id = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    example = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)