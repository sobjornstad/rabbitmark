from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Table, Integer, String, Column, ForeignKey, \
        PrimaryKeyConstraint

Base = declarative_base()

mark_tag_assoc = Table('mark_tag_assoc', Base.metadata,
        Column('mark_id', Integer, ForeignKey('bookmarks.id')),
        Column('tag_id', Integer, ForeignKey('tags.id')),
        PrimaryKeyConstraint('mark_id', 'tag_id'))

class Bookmark(Base):
    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    description = Column(String)
    tags_rel = relationship("Tag", secondary=mark_tag_assoc,
                            backref="bookmarks")

    def __repr__(self):
        return "<Bookmark named %s>" % self.name

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    def __str__(self):
        return self.text

    def __repr__(self):
        return "<Tag '%s'>" % self.text
