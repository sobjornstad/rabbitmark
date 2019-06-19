from typing import Iterable

from models import Bookmark, Tag

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
        bookmark.tags_rel.append(existing_tag)
        return existing_tag
    else:
        new_tag = Tag(text=tag)
        bookmark.tags_rel.append(new_tag)
        return new_tag


