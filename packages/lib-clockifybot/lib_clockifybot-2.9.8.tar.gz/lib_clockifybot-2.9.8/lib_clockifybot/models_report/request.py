from sqlalchemy import Column, Integer, String

from .base import Base


class Request(Base):
    __tablename__ = "request"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String)
    messages = Column(String)

    def __repr__(self):
        return f"Request('{self.request_id}', '{self.messages}')"
