
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .base import Base

class Gift(Base):
    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True)
    gift_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Gift(id={self.id}, name={self.name}, price={self.price})>"

__all__ = ['Gift']