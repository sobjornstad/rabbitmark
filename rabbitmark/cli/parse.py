"""
parse.py - parse command-line options
"""

import argparse
from typing import Sequence
import webbrowser

# pylint: disable=no-name-in-module
import pyperclip
from tabulate import tabulate

from rabbitmark.definitions import SearchMode
from rabbitmark.librm import bookmark
from rabbitmark.librm import database


def find_handler(session, args: argparse.Namespace) -> str:
    if args.filter:
        filter_text = '%' + args.filter + '%'
    else:
        filter_text = '%'
    
    tags = args.tag or []
    mode = SearchMode.And if getattr(args, 'and') else SearchMode.Or

    marks = bookmark.find_bookmarks(session, filter_text, tags, True, mode)
    result_rows = sorted(
        ((i.id, i.name, ', '.join(str(j) for j in i.tags)) for i in marks),
        key=lambda i: i[1])
    headers = ["ID", "Name", "Tags"]
    return tabulate(result_rows, headers)


def _act_on_id(session, id_, func) -> None:
    """
    Find a bookmark with ID /id/. Show an error if it doesn't exist, or call
    /func/ on it if it does.
    """
    mark = bookmark.get_bookmark_by_id(session, id_)
    if mark is None:
        print("No bookmark with ID {id_} was found. (Try 'rabbitmark find'?)")
    else:
        func(mark)


def go_handler(session, args: argparse.Namespace) -> None:
    "Browse to the URL of the specified bookmark."
    _act_on_id(session, args.id,
               lambda mark: webbrowser.open(mark.url, new=2, autoraise=True))


def copy_handler(session, args: argparse.Namespace) -> None:
    "Copy the URL of the specified bookmark."
    def on_mark(mark):
        pyperclip.copy(mark.url)
        print(f"URL copied to clipboard: {mark.url}")
    _act_on_id(session, args.id, on_mark)


def get_parser() -> argparse.ArgumentParser:
    "Create the command-line parser."
    parser = argparse.ArgumentParser(description="RabbitMark CLI (use 'rabbitmark' alone to launch the GUI)")
    subparsers = parser.add_subparsers()

    find = subparsers.add_parser('find', help="List bookmarks matching a search query")
    find.add_argument('-f', '--filter', type=str,
                      help="Filter string (like the box at the top of the GUI).")
    find.add_argument('-t', '--tag', type=str, action="append",
                      help="Include bookmarks with the specified tag. "
                           "Can be used multiple times.")
    find.add_argument('-a', '--and', action='store_true',
                      help="Rather than ORing together tags, AND them together.")
    find.set_defaults(func=find_handler)

    go = subparsers.add_parser('go', help="Browse to bookmark with a given ID")
    go.add_argument('id', type=int)
    go.set_defaults(func=go_handler)

    copy = subparsers.add_parser('copy',
                                 help="Copy the URL of bookmark with a given ID")
    copy.add_argument('id', type=int)
    copy.set_defaults(func=copy_handler)

    return parser


def call(args: Sequence[str] = None) -> str:
    """
    Make a call to the CLI with arguments /args/. If /args/ is not specified,
    sys.argv is used.

    The handler function returns a list of strings, which are returned
    so that the caller of call() can display the result to stdout.
    """
    parser = get_parser()
    parsed_args = parser.parse_args(args)
    sessionmaker = database.make_Session()
    session = sessionmaker()
    return parsed_args.func(session, parsed_args)
