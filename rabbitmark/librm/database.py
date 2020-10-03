"""
database.py - general database management
"""

# pylint: disable=no-name-in-module
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SessionType

from .models import Base


# http://stackoverflow.com/questions/9671490/
# how-to-set-sqlite-pragma-statements-with-sqlalchemy
#pylint: disable=unused-argument
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    "Set SQLite pragma options for RabbitMark execution."
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def make_Session() -> SessionType:
    "Create a SQLAlchemy Session object, from which sessions can be spawned."
    engine = create_engine('sqlite:///sorenmarks-test.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing tables/dbs
    return Session
