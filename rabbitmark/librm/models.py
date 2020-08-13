# This file is part of RabbitMark.
# Copyright 2015, 2019 Soren Bjornstad. All rights reserved.

"""
models.py - SQLAlchemy ORM database model for RabbitMark
"""

#pylint: disable=invalid-name

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, Boolean, \
        Table, Column, ForeignKey, PrimaryKeyConstraint

Base = declarative_base()
mark_tag_assoc = Table(
    'mark_tag_assoc',
    Base.metadata,
    Column('mark_id', ForeignKey('bookmarks.id'), primary_key=True),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True))


class Bookmark(Base):
    "Entries for sites we want to keep track of."
    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    description = Column(String)
    tags = relationship("Tag",
                        secondary=mark_tag_assoc,
                        back_populates="bookmarks")
    private = Column(Boolean)

    def __repr__(self):
        return "<Bookmark named %s>" % self.name


class Tag(Base):
    "Tags applied to bookmarks to organize them."
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    bookmarks = relationship("Bookmark",
                             secondary=mark_tag_assoc,
                             back_populates="tags")

    def __str__(self):
        return self.text

    def __repr__(self):
        return "<Tag '%s'>" % self.text