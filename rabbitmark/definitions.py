"""
definitions.py - globally used constants and enumeration types
"""

from enum import Enum, unique

DATE_FORMAT = '%Y-%m-%d'  #: format used to display dates to the user
MYVERSION = "0.2.1"       #: current version of RabbitMark
NOTAGS = "(no tags)"      #: string used for the "untagged" filter entry in the sidebar

@unique
class SearchMode(Enum):
    "When doing a tag search with multiple tags selected, how are they combined?"
    Or = 0
    And = 1
