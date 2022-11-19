"""
interchange.py - import or export from data-interchange formats
"""

import csv
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rabbitmark.definitions import SearchMode
from . import bookmark


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

        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        first_data_row = next(reader)
        return CsvSchema(dialect, reader.fieldnames, first_data_row)


def import_bookmarks_from_csv(session, target_path: str, dialect,
                              mapping: List[Optional[str]]) -> Tuple[int, int]:
    """
    Import bookmarks from the CSV file at /target_path/. If the names
    duplicate names already present, do not import those.
    (TODO: It would be nice to be able to choose whether you want to overwrite.)

    Parameters:
        session - Database session to create imported bookmarks in
        target_path - File to import from
        dialect - Dialect of CSV to import, obtained via get_csv_schema()
        mapping - A list of RabbitMark fields to map each field in the CSV file to.
            If this is ["Name", None, "URL", None, "Description"],
            the 1st, 3rd, and 5th fields of the CSV will be mapped to Name, URL,
            and Description, the 2nd and 4th fields will be ignored,
            and the Tags RabbitMark field will be left blank.

    Return:
        Tuple of (number imported, number of duplicates).

    Raises:
        Any file handling errors that may occur.
    """
    with open(target_path, 'r', newline='') as f:
        reader = csv.reader(f, dialect=dialect)
        _ = next(reader)  # skip past header row

        dupes = 0
        imported = 0
        for row in reader:
            # Create a dictionary of defined field names to values for this row.
            mark_data: Dict[str, Any] = {}
            for col_data, col_role in zip(row, mapping):
                if col_role is not None:
                    mark_data[col_role.lower()] = col_data

            # Sanity check. The UI should prevent the user from importing if
            # these fields aren't mapped.
            assert "url" in mark_data, "Missing URL role allowed in import!"
            assert "name" in mark_data, "Missing Name role allowed in import!"

            # If the bookmark exists already, ignore it.
            # TODO: It would be nice to report the content so the user can see
            # if there's an issue.
            if bookmark.url_exists(session, mark_data['url']):
                dupes += 1
                continue

            # It's a go, add the bookmark using whatever fields we've defined.
            if 'tags' in mark_data:
                mark_data['tags'] = (i.strip() for i in mark_data['tags'].split(','))
            bookmark.add_bookmark(session, **mark_data)
            imported += 1

    return imported, dupes
