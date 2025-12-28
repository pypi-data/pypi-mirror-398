from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from .base import Base
from .workspace import Workspace


class UserReport(Base):
    __tablename__ = "user_report"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True)
    username = Column(String)
    api_key = Column(String)
    coolname = Column(String)
    role = Column(String)
    added_by_chat_id = Column(String)
    challenge = Column(Boolean, nullable=False, default=False)
    command = Column(String)
    clock = Column(String)
    is_active_clock = Column(Boolean, nullable=False, default=False)
    clockify_id = Column(String)
    workspaces = relationship(
        Workspace, back_populates="main_user", foreign_keys="Workspace.user_id"
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.role}', '{self.api_key}')"
