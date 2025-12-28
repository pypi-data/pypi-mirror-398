from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Identify(Base):
    __tablename__ = "identify"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("users.chat_id"), unique=True)
    username = Column(String)
    clockify_id = Column(String)

    # Relationships
    user = relationship("Users", back_populates="identify")
    leave = relationship(
        "Leave", back_populates="identify", uselist=False, cascade="all, delete-orphan"
    )
