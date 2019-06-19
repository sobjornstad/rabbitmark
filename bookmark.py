from typing import Iterable

from models import Bookmark, Tag
import utils


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


def maybe_expunge_tag(session, tag: Tag) -> bool:
    """
    Delete /tag/ from the tags table if it is no longer referenced by
    any bookmarks.

    Return:
        True if the tag was deleted.
        False if the tag is still referenced and was not deleted.
    """
    if not tag.bookmarks:
        session.delete(tag)
        return True
    else:
        return False
