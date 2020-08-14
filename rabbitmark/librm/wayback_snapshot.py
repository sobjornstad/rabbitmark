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
    def __init__(self, original_url: str, time: datetime.datetime, page_path: str):
        self.original_url = original_url  #: The live URL this is a snapshot of.
        self.time = time                  #: The time the snapshot was taken.
        self.page_path = page_path        #: Path to the page in the WBM.

        #: Timestamp as a string, as used within the WBM to identify the snapshot.
        self.raw_timestamp = self.time.strftime(r'%Y%m%d%H%M%S')

    def __repr__(self) -> str:
        return (f"<WaybackSnapshot [{self.page_path}] @[{self.raw_timestamp}] "
                f"path={self.page_path}>")

    @classmethod
    def from_api_return(cls, original_url: str, data_row: Tuple) -> 'WaybackSnapshot':
        "Generate a Snapshot object from the return of the CDX API."
        timestamp, page_path = data_row[1:3]
        dt = datetime.datetime.strptime(timestamp, r'%Y%m%d%H%M%S')
        return cls(original_url, dt, page_path)

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
    <WaybackSnapshot [https://controlaltbackspace.org/] @[20191220103606] path=https://controlaltbackspace.org/>
    """

    result = requests.get(CDX_SEARCH_ENDPOINT,
                          params={'url': original_url, 'output': 'json'})
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
