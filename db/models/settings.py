from sqlalchemy import Column, Integer, Boolean, DateTime
from .base import Base
from datetime import datetime


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, primary_key=True)
    notifications_enabled = Column(Boolean, default=True)
    update_frequency = Column(Integer, default=60)
    last_check = Column(DateTime, default=datetime.min)

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, notifications={self.notifications_enabled}, freq={self.update_frequency}min)>"


__all__ = ['UserSettings']