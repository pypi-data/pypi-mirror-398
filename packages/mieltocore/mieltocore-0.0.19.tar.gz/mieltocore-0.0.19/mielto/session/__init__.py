from typing import Union

from mielto.session.agent import AgentSession
from mielto.session.summary import SessionSummaryManager
from mielto.session.team import TeamSession
from mielto.session.workflow import WorkflowSession

Session = Union[AgentSession, TeamSession, WorkflowSession]

__all__ = ["AgentSession", "TeamSession", "WorkflowSession", "Session", "SessionSummaryManager"]
