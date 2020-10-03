"""
tag.py -- RabbitMark tag operations
"""

from typing import Sequence

from rabbitmark.definitions import NOTAGS
from .models import Tag, Bookmark


def change_tags(session, existing_bookmark: Bookmark, new_tags: Sequence[str]) -> None:
    """
    Replace the tags on /existing_bookmark/ with the list of /new_tags/.
    """
    # remove tags that are no longer used
    for tag in existing_bookmark.tags[:]:
        if tag.text not in new_tags:
            existing_bookmark.tags.remove(tag)
            maybe_expunge_tag(session, tag)
    session.flush()

    # add new tags
    for tag in new_tags:
        existing_tag = session.query(Tag).filter(Tag.text == tag).first()
        if existing_tag:
            existing_bookmark.tags.append(existing_tag)
        else:
            new_tag = Tag(text=tag)
            session.add(new_tag)
            existing_bookmark.tags.append(new_tag)


def delete_tag(session, tag_name: str) -> None:
    """
    Delete a tag from all bookmarks.
    """
    tag_obj = session.query(Tag).filter(Tag.text == tag_name).one()
    session.delete(tag_obj)


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


def merge_tags(session, from_name: str, into_name: str) -> bool:
    """
    Merge the tag from_name into to_name. If the target doesn't exist,
    DWIM and do a rename instead.
    """
    from_tag = session.query(Tag).filter(Tag.text == from_name).one()
    to_tag = session.query(Tag).filter(Tag.text == into_name).one_or_none()

    if to_tag is None:
        return rename_tag(session, from_name, into_name)

    bquery = session.query(Bookmark)
    needs_retag = bquery.filter(Bookmark.tags.any(Tag.text == from_name)).all()
    for mark in needs_retag:
        mark.tags.remove(from_tag)
        mark.tags.append(to_tag)

    session.delete(from_tag)
    session.flush()
    return True


def rename_tag(session, current_name: str, new_name: str) -> bool:
    """
    Rename tag /tag/ to /new/.

    Return:
        True if tag was renamed.
        False if another tag already existed with name /new/ or it is
            otherwise invalid (there are no other checks currently).
    """
    existing_tag = session.query(Tag).filter(Tag.text == new_name).one_or_none()
    if existing_tag is not None:
        return False

    tag_obj = session.query(Tag).filter(Tag.text == current_name).one()
    tag_obj.text = new_name
    return True


def scan_tags(session, show_private: bool) -> Sequence[str]:
    """
    Get a list of the names of all existing tags, plus the NOTAGS placeholder.
    Don't show private tags if told we are hiding private tags.
    """
    q = session.query(Tag)
    if not show_private:
        # pylint: disable=singleton-comparison
        q = q.filter(Tag.bookmarks.any(Bookmark.private == False))
    tag_list = [str(i) for i in q.all()]
    tag_list.append(NOTAGS)
    return tag_list
