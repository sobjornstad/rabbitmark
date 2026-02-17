"""
readwise.py - save bookmarks to Readwise Reader
"""

from typing import Any, Dict, List, Optional

import requests

SAVE_ENDPOINT = "https://readwise.io/api/v3/save/"


def save_to_reader(
    api_token: str,
    url: str,
    title: str,
    summary: str = "",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Save a URL to Readwise Reader's reading list.

    Returns the response dict on success, raises on failure.
    """
    headers = {
        "Authorization": f"Token {api_token}",
    }
    payload: Dict[str, Any] = {
        "url": url,
        "title": title,
        "location": "later",
    }
    if summary:
        payload["summary"] = summary
    if tags:
        payload["tags"] = tags

    result = requests.post(
        SAVE_ENDPOINT, json=payload, headers=headers, timeout=30
    )
    if not result.ok:
        try:
            detail = result.json()
        except ValueError:
            detail = result.text
        raise RuntimeError(
            f"Readwise Reader returned {result.status_code}: {detail}"
        )
    return result.json()
