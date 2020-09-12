"""
config.py - manage config values
"""

from .models import Config


def get(session, key: str) -> str:
    """
    Retrieve the stringly-typed value of a configuration key,
    or None if it is NULL or doesn't exist.
    """
    pair = session.query(Config).filter(Config.key == key).one_or_none()
    return pair.value if pair is not None else None


def put(session, key: str, value: str) -> None:
    "Set the stringly-typed value of a configuration key."
    pair = session.query(Config).filter(Config.key == key).one_or_none()
    if pair is None:
        pair = Config(key=key, value=value)
        session.add(pair)
    else:
        pair.value = value
        session.flush()


def exists(session, key: str) -> bool:
    "Check if a given configuration key exists and is not NULL."
    pair = session.query(Config).filter(Config.key == key).one_or_none()
    return pair is not None
