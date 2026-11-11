"""Tests for CLI `find -f`: filter text is a literal substring match.

SQL LIKE wildcards (``%``, ``_``, ``\\``) typed by the user must not act
as wildcards (see ``rabbitmark.cli.parse._escape_like``).
"""

import os

import pytest

import rabbitmark.cli
from rabbitmark.librm import bookmark, database


@pytest.fixture()
def seeded_db(tmp_path, monkeypatch):
    """Seeded throwaway database with names containing LIKE specials."""
    monkeypatch.setenv("RABBITMARK_DATABASE", str(tmp_path / "rm.db"))
    session = database.make_Session()()
    bookmark.add_bookmark(session, "https://example.com/a", [],
                          name="100% real")
    bookmark.add_bookmark(session, "https://example.com/b", [],
                          name="100x other")
    bookmark.add_bookmark(session, "https://example.com/c", [],
                          name="under_score")
    bookmark.add_bookmark(session, "https://example.com/d", [],
                          name="underscore")
    session.commit()
    session.close()
    return tmp_path


def test_percent_is_literal(seeded_db):
    result = rabbitmark.cli.call(["find", "-f", "100%"])
    assert "100% real" in result
    assert "100x other" not in result


def test_underscore_is_literal(seeded_db):
    result = rabbitmark.cli.call(["find", "-f", "under_score"])
    assert "under_score" in result
    assert "underscore" not in result


def test_plain_substring_still_matches(seeded_db):
    result = rabbitmark.cli.call(["find", "-f", "real"])
    assert "100% real" in result
