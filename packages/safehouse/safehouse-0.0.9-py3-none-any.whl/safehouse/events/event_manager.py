import logging

from .event import Event, EventType
from safehouse import config
from safehouse.services.client import events as events_service


logger = logging.Logger(__name__)


class EventManager:
    def __init__(self, origin: str, project: str):
        self.origin = origin
        self.project = project
        self.load_events()

    def __getattr__(self, name):
        event_type = self.event_types.get(name)
        if event_type:
            return Event(event_type=event_type, origin=self.origin)
        raise AttributeError(f"'{type(self)}' object has no attribute '{name}'")

    def load_events(self):
        event_types_list = events_service.register_event_types(config.project.events)
        self.event_types = {
            e['name']: EventType(e['name'], e['version'], e['attributes'])
            for e in event_types_list
        }
        logger.info(f"registered_event_types=={self.event_types}")
