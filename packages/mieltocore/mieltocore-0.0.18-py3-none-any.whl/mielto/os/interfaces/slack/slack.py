import logging
from typing import Optional

from fastapi.routing import APIRouter

from mielto.agent.agent import Agent
from mielto.os.interfaces.base import BaseInterface
from mielto.os.interfaces.slack.router import attach_routes
from mielto.team.team import Team

logger = logging.getLogger(__name__)


class Slack(BaseInterface):
    type = "slack"

    router: APIRouter

    def __init__(self, agent: Optional[Agent] = None, team: Optional[Team] = None):
        self.agent = agent
        self.team = team

        if not self.agent and not self.team:
            raise ValueError("Slack requires an agent and a team")

    def get_router(self, **kwargs) -> APIRouter:
        # Cannot be overridden
        self.router = APIRouter(prefix="/slack", tags=["Slack"])

        self.router = attach_routes(router=self.router, agent=self.agent, team=self.team)

        return self.router
