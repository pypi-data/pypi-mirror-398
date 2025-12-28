from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Leave(Base):
    __tablename__ = "leave"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("identities.chat_id"), unique=True)
    username = Column(String)
    workday = Column(String)
    hours = Column(String)
    status = Column(String)
    mode = Column(String)
    substitute = Column(String)
    description = Column(String)
    request_id = Column(Numeric)
    is_active = Column(Boolean, default=True)

    # Relationships
    identity = relationship("Identities", back_populates="leave")
