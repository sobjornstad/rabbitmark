"""
wayback_snapshot.py - retrieve objects representing archive.org snapshots of a website
"""

import datetime
from typing import Sequence, Tuple

import requests

CDX_SEARCH_ENDPOINT = "http://web.archive.org/cdx/search/cdx"


class WaybackSnapshot:
    """
    A snapshot of a website in the WayBackMachine.
    """
    def __init__(self, original_url: str, time: datetime.datetime, page_path: str,
                 response: str) -> None:
        self.original_url = original_url  #: The live URL this is a snapshot of.
        self.time = time                  #: The time the snapshot was taken.
        self.page_path = page_path        #: Path to the page in the WBM.
        self.response = response          #: HTTP status code at crawl time

        #: Timestamp as a string, as used within the WBM to identify the snapshot.
        self.raw_timestamp = self.time.strftime(r'%Y%m%d%H%M%S')

    def __repr__(self) -> str:
        return (f"<WaybackSnapshot [{self.page_path}] @[{self.raw_timestamp}] "
                f"path={self.page_path} code={self.response}>")

    @classmethod
    def from_api_return(cls, original_url: str, data_row: Tuple) -> 'WaybackSnapshot':
        "Generate a Snapshot object from the return of the CDX API."
        timestamp, page_path, response = data_row
        dt = datetime.datetime.strptime(timestamp, r'%Y%m%d%H%M%S')
        return cls(original_url, dt, page_path, response)

    @property
    def archived_url(self) -> str:
        "URL to view the contents of the snapshot on the web."
        return f"https://web.archive.org/web/{self.raw_timestamp}/{self.page_path}"

    def formatted_timestamp(self, date_fmt: str) -> str:
        "Timestamp of this snapshot, formatted using the provided date_fmt."
        return self.time.strftime(date_fmt)


def get_snapshots(original_url: str) -> Sequence[WaybackSnapshot]:
    """
    Request a list of snapshots from the CDX WayBackMachine API on archive.org.

    Return:
        A sequence of WaybackSnapshot objects, or an empty sequence
        if none were found in the archives.

    Raises:
        An HTTP exception if we were unable to get a correct response
        (even one saying no results were found) from the WayBackMachine.

    >>> sn = get_snapshots("https://controlaltbackspace.org")
    >>> len(sn) > 1
    True
    >>> isinstance(sn[0], WaybackSnapshot)
    True
    >>> sn[0]
    <WaybackSnapshot [https://controlaltbackspace.org/] @[20191220103606] path=https://controlaltbackspace.org/ code=200>
    """
    params = {
        'url': original_url,
        'output': 'json',
        'fl': "timestamp,original,statuscode"
    }
    result = requests.get(CDX_SEARCH_ENDPOINT, params=params)
    result.raise_for_status()

    # If no results, .json() may raise ValueError or just return None.
    try:
        snapshot_data = result.json()
    except ValueError:
        return []
    if not snapshot_data:
        return []

    # First row is headers, so start after that.
    return [WaybackSnapshot.from_api_return(original_url, i)
            for i in snapshot_data[1:]]


def request_snapshot(url: str) -> None:
    """
    Ask the WayBackMachine to take a snapshot of /url/ now.

    Unfortunately there is no real API for this currently, so it's not
    possible to get the new URL, a confirmation that it succeeded, or any
    error info. I wrote to the Internet Archive asking about this, because
    they alluded to a private API in a blog post, but nobody ever got back to
    me.
    """
    r = requests.get(f"https://web.archive.org/save/{url}")
    r.raise_for_status()
