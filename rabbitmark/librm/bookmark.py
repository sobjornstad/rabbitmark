"""
bookmark.py -- RabbitMark bookmark operations
"""

from typing import Any, Dict, Iterable, Sequence

from sqlalchemy import or_

from ..utils import NOTAGS, SearchMode
from .models import Bookmark, Tag
from .tag import maybe_expunge_tag, change_tags


def add_bookmark(session, url: str, tags: Iterable[str]) -> Bookmark:
    """
    Add a new bookmark using the provided URL and tags, leaving other fields
    blank. Returns the new Bookmark object.
    """
    bookmark = Bookmark(name="", url=url, description="", private=False)
    session.add(bookmark)
    for tag in tags:
        add_tag_to_bookmark(session, bookmark, tag)
    return bookmark


def add_tag_to_bookmark(session, bookmark: Bookmark, tag: str) -> Tag:
    """
    Add the tag described by string /tag/ to the specified bookmark.
    If the tag already exists in the database, the bookmark is linked
    to that tag; otherwise, a new tag is created.

    Returns the Tag object for the new or existing tag used.
    """
    existing_tag = session.query(Tag).filter(Tag.text == tag).first()
    if existing_tag:
        bookmark.tags.append(existing_tag)
        return existing_tag
    else:
        new_tag = Tag(text=tag)
        bookmark.tags.append(new_tag)
        return new_tag


def delete_bookmark(session, bookmark: Bookmark) -> None:
    """
    Delete the specified bookmark. If the bookmark was the last to use any of
    its tags, delete the tag(s) as well.
    """
    tags = bookmark.tags
    session.delete(bookmark)
    for tag in tags:
        maybe_expunge_tag(session, tag)


def save_if_edited(session, existing_bookmark: Bookmark,
                   new_content: Dict[str, Any]) -> bool:
    """
    If the new content differs from that currently in the bookmark,
    update the bookmark to match.

    Return:
        True if an update was made, False if not.

    State change:
        The bookmark is updated on the database. The changes are not committed.
    """
    def _dirty():
        for i in ('name', 'description', 'url', 'private'):
            if getattr(existing_bookmark, i) != new_content[i]:
                return True
        if [i.text for i in existing_bookmark.tags] != new_content['tags']:
            return True
        return False

    if _dirty():
        existing_bookmark.name = new_content['name']
        existing_bookmark.description = new_content['description']
        existing_bookmark.url = new_content['url']
        existing_bookmark.private = new_content['private']

        # add new tags
        new_tags = new_content['tags']
        change_tags(session, existing_bookmark, new_tags)
        return True
    else:
        return False


# pylint: disable=singleton-comparison
def find_bookmarks(session,
                   filter_text: str,
                   tags: Sequence[str],
                   include_private: bool,
                   search_mode: SearchMode) -> Iterable[Bookmark]:
    """
    Return a list of Bookmarks in the database that match the specified
    criteria.

    /filter_text/: substring match on name, URL, or description
    /tags/: a list of tags, either OR'd or AND'd together depending on mode
    /include_private/: show private bookmarks?
    /search_mode/: describes whether to OR or AND the tags together

    Note that SQLAlchemy doesn't support in_ queries on many-to-many
    relationships, so we have to compare on the text of the tags. Conveniently,
    we are given those already!
    """

    query = session.query(Bookmark).filter(
        or_(Bookmark.name.like(filter_text),
            Bookmark.url.like(filter_text),
            Bookmark.description.like(filter_text)))

    if tags:
        if search_mode == SearchMode.And:
            if NOTAGS in tags:
                real_tags = [i for i in tags if i != NOTAGS]
                query = query.filter(Bookmark.tags == None)
            for tag in tags:
                query = query.filter(Bookmark.tags.any(Tag.text == tag))
        elif search_mode == SearchMode.Or:
            if NOTAGS in tags:
                real_tags = [i for i in tags if i != NOTAGS]
                query = query.filter(or_(
                    Bookmark.tags == None,
                    Bookmark.tags.any(Tag.text.in_(real_tags))))
            else:
                query = query.filter(Bookmark.tags.any(Tag.text.in_(tags)))
        else:
            raise AssertionError("in updateForSearch(): Search mode %r "
                                 "unimplemented" % search_mode)

    if not include_private:
        query = query.filter(Bookmark.private == False)
    return query.all()
