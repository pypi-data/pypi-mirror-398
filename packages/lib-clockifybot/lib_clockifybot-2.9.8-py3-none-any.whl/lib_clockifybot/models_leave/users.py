from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String

from .base import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True)
    username = Column(String)
    admins = Column(ARRAY(String))

    # Relationships
    identify = relationship(
        "Identify", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
