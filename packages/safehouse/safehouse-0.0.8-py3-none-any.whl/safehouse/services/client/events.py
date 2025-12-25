import datetime
import json
import logging
from typing import Dict, List

from . import events_client as client
from safehouse.types import JsonBlob


logger = logging.Logger(__name__)


def register_event_types(event_types: List[Dict[str, JsonBlob]]) -> JsonBlob:
    # register events with events service and returned version list of those events
    response = client.post(
        data=json.dumps(event_types),
        endpoint='/events/types/register/',
    )
    return response.json()


def send_event(
    *,
    attributes: JsonBlob,
    name: str,
    origin: str,
    sent_at: datetime.datetime,
    version: int,
) -> bool:
    try:
        client.post(
            data=json.dumps(
                {
                    'attributes': attributes,
                    'name': name,
                    'origin': origin,
                    'sent_at': sent_at,
                    'version': version,
                }
            ),
            endpoint='/events/',
        )
    except client.ClientError as e:
        logger.error(f"couldn't send event type '{name}.{version}': {e}")
        return False
    return True
