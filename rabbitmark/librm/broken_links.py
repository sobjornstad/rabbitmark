"""
broken_links.py - tools for checking for link rot
"""

import concurrent.futures
from typing import Callable, Optional

import requests

from .models import Bookmark


class LinkCheck:
    """
    The result of checking a link for accessibility.
    """
    def __init__(self, pk: int, name: str, url: str,
                 status_code: Optional[int] = None,
                 error_description: Optional[str] = None) -> None:
        self.pk = pk                    #: primary key of bookmark in database
        self.name = name                #: name of bookmark
        self.url = url                  #: url of page
        self.status_code = status_code  #: HTTP status code, if we got that far
        #: description of an error that prevented an HTTP status code, e.g., timed out
        self.error_description = error_description

    @property
    def successful(self) -> bool:
        return self.status_code == 200

    def __str__(self) -> str:
        if self.successful:
            return f"[ OK ] [200] {self.name} ({self.url})"
        elif self.status_code is not None:
            return f"[FAIL] [{self.status_code}] {self.name} ({self.url})"
        else:
            return f"[FAIL] [ERR] {self.error_description}: {self.name} ({self.url})"


def _get_user_agent():
    """
    When checking for link rot, some websites will return a 403 if we are
    honest and say we're Python's requests library, which makes the list
    inaccurate. To avoid this, we can pretend to be a real browser. The
    browser we're pretending to be can be adjusted with this string.

    See <https://en.wikipedia.org/wiki/User_agent#User_agent_spoofing>. This
    is a very simple way of bypassing the checks and can easily be detected
    by an attentive server; our intent is not to get into a web-scraping war
    with anyone!
    """
    return ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/83.0.4103.97 Safari/537.36')


# pylint: disable=too-many-return-statements
def _check(pk: int, name: str, url: str) -> LinkCheck:
    """
    Given the url /url/, check to see if it accessible, and return a LinkCheck
    object with the URL, primary key, and name, as well as the results of the check.
    """
    headers = {
        'User-Agent': _get_user_agent()
    }
    try:
        r = requests.head(url, timeout=10, allow_redirects=True, headers=headers)
    except requests.exceptions.SSLError:
        return LinkCheck(pk, name, url, None, "Invalid SSL certificate")
    except requests.exceptions.ConnectionError:
        return LinkCheck(pk, name, url, None, "Connection error")
    except requests.exceptions.TooManyRedirects:
        return LinkCheck(pk, name, url, None, "Redirect loop")
    except requests.exceptions.Timeout:
        return LinkCheck(pk, name, url, None, "Timed out")
    except requests.exceptions.HTTPError as e:
        return LinkCheck(pk, name, url, None, str(e))
    except requests.exceptions.RequestException as e:
        return LinkCheck(pk, name, url, None, str(e))
    else:
        return LinkCheck(pk, name, url, r.status_code, r.reason)


def scan(session, callback: Callable[[int, int, LinkCheck], None],
         only_failures: bool = False) -> None:
    """
    Retrieve all bookmarks from the session /session/ and check their URLs in
    parallel. Whenever a result comes back, call the /callback/ function of
    three parameters with the number of the current item (indexed by time),
    the total number of items, and the LinkCheck object.

    If /only_failures/ is set, only items which have failed will trigger a
    callback; the items with no issues will never be returned to the caller.
    """
    # pylint: disable=singleton-comparison
    marks = session.query(Bookmark).filter(Bookmark.skip_linkcheck == False).all()

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        for mark in marks:
            future = executor.submit(_check, pk=mark.id, name=mark.name, url=mark.url)
            futures.append(future)

        for idx, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            if (not fut.result().successful) or (not only_failures):
                callback(idx, len(marks), fut.result())
