"""
tag.py -- RabbitMark tag operations
"""

from typing import Sequence

from ..utils import NOTAGS
from .models import Tag


def delete_tag(session, tag_name: str) -> None:
    """
    Delete a tag from all bookmarks.
    """
    tag_obj = session.query(Tag).filter(Tag.text == tag_name).one()
    session.delete(tag_obj)
    session.commit()


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
    session.commit()
    return True


def scan_tags(session) -> Sequence[str]:
    "Get a list of the names of all existing tags, plus the NOTAGS placeholder."
    tag_list = [str(i) for i in session.query(Tag).all()]
    tag_list.append(NOTAGS)
    return tag_list
