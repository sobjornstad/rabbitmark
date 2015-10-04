from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Column

Base = declarative_base()

class Bookmark(Base):
    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    tags = Column(String)
    description = Column(String)

    def __repr__(self):
        return "<Bookmark named %s>" % self.name
