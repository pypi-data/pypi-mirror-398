from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    clockify_user_id = Column(String)
    name = Column(String)

    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    workspace = relationship("Workspace", foreign_keys="Team.workspace_id")

    def __repr__(self):
        return f"Team('{self.name}')"
