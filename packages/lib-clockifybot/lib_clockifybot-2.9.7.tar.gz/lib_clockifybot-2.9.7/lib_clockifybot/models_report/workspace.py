from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .team import Team


class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True, index=True)
    clockify_id = Column(String)
    name = Column(String)
    selected = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey("user_report.id"), nullable=False)
    main_user = relationship("UserReport", foreign_keys="Workspace.user_id")
    teams = relationship(
        Team, back_populates="workspace", foreign_keys="Team.workspace_id"
    )

    def __repr__(self):
        return f"Workspace('{self.name}', '{self.clockify_id}')"
