import json
import logging
import requests
from typing import List, Optional

from safehouse.types import JsonBlob


logger = logging.Logger(__name__)
EVENTS_URL = "http://localhost:9000"


class ClientError(Exception):
    def __init__(self, detail):
        super().__init__(detail)


def headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def post(
        *,
        data: Optional[JsonBlob] = None,
        endpoint: str,
        headers: Optional[JsonBlob] = headers(),
        query_params: Optional[JsonBlob] = None,
        acceptable_status_codes: Optional[List[int]] = [200],
) -> requests.Response:
        response = requests.post(
            EVENTS_URL + endpoint,
            headers=headers,
            data=data,
        )
        validate_response(response, acceptable_status_codes=acceptable_status_codes)
        return response


def validate_response(
        response: requests.Response,
        acceptable_status_codes: Optional[List[int]] = [200],
):
    if response.status_code not in acceptable_status_codes:
        error_string = str(response)
        error_detail = error_string
        try:
            error_string = response.json()
            if type(error_string) == list:
                error_detail = ', '.join(error_string)
            else:
                error_detail = error_string['detail']
        except json.JSONDecodeError:
            pass
        raise ClientError(error_detail)
