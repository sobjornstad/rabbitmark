"""
interchange.py - import or export from data-interchange formats
"""

import csv
from dataclasses import dataclass
from typing import Dict, List

from . import bookmark
from ..utils import SearchMode


@dataclass
class CsvSchema:
    "Structure describing a preview of a CSV file to be imported."
    dialect: csv.Dialect
    columns: List[str]
    first_data_row: Dict[str, str]


def export_bookmarks_to_csv(session, target_path: str) -> int:
    """
    Export all bookmarks to the CSV file at /target_path/, overwriting
    the file if it exists.

    Return:
        The number of bookmarks exported.

    Raises:
        Any file handling errors that may occur.
    """
    with open(target_path, "w") as f:
        names = ["name", "url", "description", "tags"]
        writer = csv.DictWriter(f, fieldnames=names, delimiter=',', quotechar='"')
        writer.writeheader()
        marks = list(bookmark.find_bookmarks(session, "%", [], True, SearchMode.And))
        for mark in marks:
            writer.writerow({
                "name": mark.name,
                "url": mark.url,
                "description": '\\n'.join(mark.description.split('\n')),
                "tags": ','.join(str(i) for i in mark.tags),
            })

    return len(marks)


def get_csv_schema(target_path: str) -> CsvSchema:
    """
    Given a file path, inspect it and return a schema class describing the
    format of the file, including its 'csv' module dialect, its column names,
    and the first row of data as a preview.
    """
    with open(target_path, 'r', newline='') as f:
        sample = f.readline()
        dialect = csv.Sniffer().sniff(sample)
        has_header = csv.Sniffer().has_header(sample)

        if not has_header:
            return dialect, None, None
        else:
            f.seek(0)
            reader = csv.DictReader(f, dialect=dialect)
            header_row = next(reader)
            first_data_row = next(reader)
            return CsvSchema(dialect, list(header_row.keys()), first_data_row)


def import_bookmarks_from_csv(session, target_path: str) -> int:
    """
    Import bookmarks from the CSV file at /target_path/.

    Return:
        The number of bookmarks imported.
    
    Raises:
        Any file handling errors that may occur.
    """