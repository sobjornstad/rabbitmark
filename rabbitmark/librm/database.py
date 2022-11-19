"""
database.py - general database management
"""

import os
from pathlib import Path
import platform

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


def _get_datadir() -> Path:
    this_os = platform.system()
    if this_os == 'Windows':
        path = Path(os.path.expandvars("%APPDATA%\\RabbitMark"))
    elif this_os == 'Darwin':
        path = Path(os.path.expanduser("~/Library/RabbitMark"))
    elif this_os == 'Linux':
        xdg_home = os.environ.get('XDG_DATA_HOME', str(Path.home() / ".local"))
        path = Path(xdg_home) / "share" / "RabbitMark"
    else:
        # try to fall back, but no guarantees at this point...
        path = Path(os.path.expanduser("~/.rabbitmark"))
    return path


def make_Session() -> SessionType:
    "Create a SQLAlchemy Session object, from which sessions can be spawned."
    path_from_env = os.environ.get("RABBITMARK_DATABASE", None)
    if path_from_env:
        database_path = path_from_env
    else:
        folder = str(_get_datadir())
        if not os.path.isdir(folder):
            os.mkdir(folder)
        database_path = folder + "/rabbitmark.db"

    sqlite_uri = f"sqlite:///{database_path}"
    engine = create_engine(sqlite_uri)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing tables/dbs
    return Session
