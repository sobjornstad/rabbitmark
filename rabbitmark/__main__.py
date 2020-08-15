"""
RabbitMark - main module
Copyright (c) 2015, 2018, 2019, 2020 Soren Bjornstad.

All rights reserved (temporary; if you read this and want such, contact me
for relicensing under some FOSS license).
"""

# pylint: disable=no-name-in-module
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SessionType

from .librm.models import Base
from . import main_window


def make_Session() -> SessionType:
    "Create a SQLAlchemy Session object, from which sessions can be spawned."
    engine = create_engine('sqlite:///sorenmarks-test.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing tables/dbs
    return Session


# http://stackoverflow.com/questions/9671490/
# how-to-set-sqlite-pragma-statements-with-sqlalchemy
#pylint: disable=unused-argument
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    "Set SQLite pragma options for RabbitMark execution."
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


sessionmaker = make_Session()
main_window.start(sessionmaker)
