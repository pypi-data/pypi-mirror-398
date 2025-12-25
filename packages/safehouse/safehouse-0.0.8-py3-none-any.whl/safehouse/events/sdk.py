import logging

from safehouse import config
from .event_manager import EventManager


logger = logging.Logger(__name__)


def init(
    *,
    origin: str,
) -> EventManager:
    project = config.project
    if not project:
        raise Exception("no project defined")
    return EventManager(origin, project)
