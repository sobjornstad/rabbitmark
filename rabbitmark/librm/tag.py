"""
tag.py -- RabbitMark tag operations
"""

from typing import Sequence

from sqlalchemy import func

from rabbitmark.definitions import NOTAGS
from .models import Tag, Bookmark, mark_tag_assoc


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


def scan_tags_with_counts(session, show_private: bool) -> dict[str, int]:
    """
    Get a dict mapping tag names to their bookmark counts, plus the NOTAGS
    placeholder. When show_private is False, count only non-private bookmarks;
    tags with zero visible bookmarks are excluded.
    """
    # pylint: disable=singleton-comparison
    q = (
        session.query(Tag.text, func.count(mark_tag_assoc.c.mark_id))
        .join(mark_tag_assoc, Tag.id == mark_tag_assoc.c.tag_id)
        .join(Bookmark, Bookmark.id == mark_tag_assoc.c.mark_id)
    )
    if not show_private:
        q = q.filter(Bookmark.private == False)
    q = q.group_by(Tag.text)
    result = dict(q.all())

    # Count bookmarks with no tags at all.
    notags_q = session.query(func.count(Bookmark.id)).filter(~Bookmark.tags.any())
    if not show_private:
        notags_q = notags_q.filter(Bookmark.private == False)
    result[NOTAGS] = notags_q.scalar()

    return result
