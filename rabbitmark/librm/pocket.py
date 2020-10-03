"""
pocket.py - integration with the Pocket read-it-later service
"""

import json
from typing import Callable, Dict, Iterable, List, Tuple, Union

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
    add_endpoint = "https://getpocket.com/v3/add"
    get_endpoint = "https://getpocket.com/v3/get"

    def __init__(self, session):
        self.consumer_key = config.get(session, "pocket_consumer_key")
        self.access_token = config.get(session, "pocket_access_token")

    def valid(self) -> bool:
        "Check if the configuration is valid."
        return (self.consumer_key is not None
                and self.access_token is not None
                and self.add_endpoint is not None
                and self.get_endpoint is not None)


def _wrap_request(request_func: Callable):
    """
    Wrap the requests call in request_func in some error-handling logic.
    Return tuple:

    [0] the request return value
    [1] True if successful, False if not
    [2] An error message (or an empty string if successful)
    """
    try:
        r = request_func()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return r, False, ("Unable to connect to Pocket. "
                          "Please check your network connection.")
    except requests.exceptions.RequestException as e:
        return r, False, (f"Unknown error from Python requests: {str(e)}")

    if r.status_code == 200:
        return r, True, ""
    elif r.status_code == 401:
        return r, False, ("Unable to authenticate to the Pocket API. "
                          "Please check your Pocket configuration.")
    elif r.status_code == 403:
        return r, False, (
            "Unable to authenticate to the Pocket API. Please check your "
            "Pocket configuration.\n\nIf you're sure your configuration is "
            "right, and you've been adding a lot of items to Pocket, "
            "it's also possible you're being rate-limited. In that case, "
            "wait an hour and try again.")
    elif r.status_code == 503:
        # Find it hard to believe this will ever happen scheduled nowadays,
        # but their API docs says it's a possible message...
        return r, False, "Pocket is down for maintenance. Please try again later."
    else:
        return r, False, r.json()['X-Error']


def add_url(pconf: PocketConfig, mark: Bookmark,
            tags: Iterable[str]) -> Tuple[bool, str]:
    """
    Add the URL of a bookmark to the user's Pocket reading list.

    Parameters:
        pconf - An instance of PocketConfig, containing the API keys, etc.
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

    return _wrap_request(
        lambda: requests.post(url=pconf.add_endpoint, data=my_json, headers=my_headers)
        )[1:]


def sync_items(
        session,
        pconf: PocketConfig,
        get_only_tag: str = None,
        get_only_favorites: bool = False,
        get_only_since: bool = True,
        use_excerpt: bool = False,
        tag_with: str = None,
        tag_passthru: bool = False,
        discard_pocket_tags: str = None) \
        -> Tuple[bool, Union[List[Dict[str, str]], str]]:
    """
    Retrieve items from Pocket that match the provided criteria.

    Return tuple:
        [0] True if successful, False if failed.
        [1] A list of dictionaries containing the relevant article data if successful,
            or a string error message if failed.
    """
    if not pconf.valid():
        raise InvalidConfigurationError()

    params = {
        "consumer_key": pconf.consumer_key,
        "access_token": pconf.access_token,
        "state": "all",  # not just unread
        "detailType": "complete",  # otherwise no tags
    }
    if get_only_favorites:
        params['favorite'] = 1
    if get_only_tag is not None:
        params['tag'] = get_only_tag
    if get_only_since:
        since = config.get(session, "pocket_since")
        if since is not None:
            params['since'] = since

    my_json = json.dumps(params)
    my_headers = {
        "Content-Type": "application/json",
        "X-Accept": "application/json",
    }

    r, successful, _ = _wrap_request(
        lambda: requests.post(url=pconf.get_endpoint, data=my_json, headers=my_headers)
    )
    if not successful:
        return False, ""

    response = r.json()

    # Bizarrely, returns an empty list if no results,
    # or an _object_ mapping ids to result objects if there are results.
    if not response['list']:
        return True, []

    articles = []
    for site in response['list'].values():
        if 'tags' in site:
            pocket_tags = set(site['tags'].keys())
        else:
            # Sometimes not present for no apparent reason
            pocket_tags = set()
        rabbitmark_tags = []
        if tag_with:
            rabbitmark_tags.append(tag_with)
        if tag_passthru:
            if discard_pocket_tags:
                pocket_discard_set = set(
                    i.strip() for i in discard_pocket_tags.split(','))
                rabbitmark_tags.extend(pocket_tags.difference(pocket_discard_set))
            else:
                rabbitmark_tags.extend(pocket_tags)

        articles.append({
            "name": site['resolved_title'] or site['given_title'],
            "url": site['resolved_url'],
            "description": site['excerpt'] if use_excerpt else "",
            "tags": rabbitmark_tags,
        })

    config.put(session, "pocket_since", response['since'])
    return True, articles
