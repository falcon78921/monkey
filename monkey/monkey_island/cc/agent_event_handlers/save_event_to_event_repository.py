import logging

from common.agent_events import AbstractAgentEvent
from monkey_island.cc.repository import IAgentEventRepository

logger = logging.getLogger(__name__)


class save_event_to_event_repository:
    def __init__(self, event_repository: IAgentEventRepository):
        self._event_repository = event_repository

    def __call__(self, event: AbstractAgentEvent):
        self._event_repository.save_event(event)
