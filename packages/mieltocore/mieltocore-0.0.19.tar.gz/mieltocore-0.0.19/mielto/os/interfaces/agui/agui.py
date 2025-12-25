"""Main class for the AG-UI app, used to expose an Mielto Agent or Team in an AG-UI compatible format."""

from typing import Optional

from fastapi.routing import APIRouter

from mielto.agent import Agent
from mielto.os.interfaces.agui.router import attach_routes
from mielto.os.interfaces.base import BaseInterface
from mielto.team import Team


class AGUI(BaseInterface):
    type = "agui"

    router: APIRouter

    def __init__(self, agent: Optional[Agent] = None, team: Optional[Team] = None):
        self.agent = agent
        self.team = team

        if not self.agent and not self.team:
            raise ValueError("AGUI requires an agent and a team")

    def get_router(self, **kwargs) -> APIRouter:
        # Cannot be overridden
        self.router = APIRouter(tags=["AGUI"])

        self.router = attach_routes(router=self.router, agent=self.agent, team=self.team)

        return self.router
