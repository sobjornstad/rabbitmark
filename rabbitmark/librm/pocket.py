"""
pocket.py - integration with the Pocket read-it-later service
"""

import json
from typing import Iterable, Tuple

import requests

from .bookmark import Bookmark
from . import config


class InvalidConfigurationError(Exception):
    pass


class PocketConfig:
    """
    API information for connecting to Pocket.
    Some is hard-coded, other items are retrieved from the user's configuration table.
    """
    endpoint = "https://getpocket.com/v3/add"

    def __init__(self, session):
        self.consumer_key = config.get(session, "pocket_consumer_key")
        self.access_token = config.get(session, "pocket_access_token")

    def valid(self) -> bool:
        "Check if the configuration is valid."
        return (self.consumer_key is not None
                and self.access_token is not None
                and self.endpoint is not None)


def add_url(pconf: PocketConfig, mark: Bookmark,
            tags: Iterable[str]) -> Tuple[bool, str]:
    """
    Add the URL of a bookmark to the user's Pocket reading list.

    Parameters:
        config - An instance of PocketConfig, containing the API keys, etc.
        mark - A bookmark to send to Pocket.
        tags - Iterable of Pocket tags to assign to the new item.
            These need not correspond with RabbitMark tags.

    Return tuple:
        [0] Whether the operation succeeded.
        [1] Error message, if the operation did not succeed.

    Raises:
        InvalidConfigurationError, if the pconf provided isn't valid.
        You can also check this yourself ahead of time with pconf.valid().
    """
    if not pconf.valid():
        raise InvalidConfigurationError()

    my_json = json.dumps({
        "url": mark.url,
        "title": mark.name,
        "tags": ', '.join(i.replace(',', '_') for i in tags),
        "consumer_key": pconf.consumer_key,
        "access_token": pconf.access_token,
    })
    my_headers = {
        "Content-Type": "application/json",
        "X-Accept": "application/json",
    }

    try:
        r = requests.post(url=pconf.endpoint, data=my_json, headers=my_headers)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False, ("Unable to connect to Pocket. "
                       "Please check your network connection.")
    except requests.exceptions.RequestException as e:
        return False, (f"Unknown error from Python requests: {str(e)}")

    if r.status_code == 200:
        return True, ""
    elif r.status_code == 401:
        return False, ("Unable to authenticate to the Pocket API. "
                       "Please check your Pocket configuration.")
    elif r.status_code == 403:
        return False, ("Unable to authenticate to the Pocket API. Please check your "
                       "Pocket configuration.\n\nIf you're sure your configuration is "
                       "right, and you've been adding a lot of items to Pocket, "
                       "it's also possible you're being rate-limited. In that case, "
                       "wait an hour and try again.")
    elif r.status_code == 503:
        # Find it hard to believe this will ever happen scheduled nowadays,
        # but their API docs says it's a possible message...
        return False, "Pocket is down for maintenance. Please try again later."
    else:
        return False, r.json()['X-Error']
