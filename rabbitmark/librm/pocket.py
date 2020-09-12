"""
pocket.py - integration with the Pocket read-it-later service
"""

import json
from typing import Iterable

import requests

from .bookmark import Bookmark

class PocketConfig:
    endpoint = "https://getpocket.com/v3/add"

    def __init__(self):
        # TODO: Don't hard-code these :)
        self.consumer_key = ""
        self.access_token = ""


def add_url(config: PocketConfig, mark: Bookmark, tags: Iterable[str]) -> None:
    """
    Add the URL of a bookmark to the user's Pocket reading list.

    Parameters:
        config - An instance of PocketConfig, containing the API keys, etc.
        mark - A bookmark to send to Pocket.
        tags - Pocket tags to assign to the new item.
    """
    my_json = json.dumps({
        "url": mark.url,
        "title": mark.name,
        "tags": ', '.join(i.replace(',', '_') for i in tags),
        "consumer_key": config.consumer_key,
        "access_token": config.access_token,
    })
    my_headers = {
        "Content-Type": "application/json",
        "X-Accept": "application/json",
    }
    r = requests.post(url=config.endpoint, data=my_json, headers=my_headers)
    r.raise_for_status()
