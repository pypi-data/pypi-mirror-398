from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from .base import Base


class Identities(Base):
    __tablename__ = "identities"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String)
    username = Column(String)
    clockify_ids = Column(MutableList.as_mutable(JSONB))

    # Relationships
    leave = relationship(
        "Leave", back_populates="identity", uselist=False, cascade="all, delete-orphan"
    )
