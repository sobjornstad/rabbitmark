"""
bookmark_table - model for a table showing all (or filtered) bookmarks
"""

from enum import Enum, unique
from typing import Any, Callable, Optional, List

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractTableModel, pyqtSignal

from rabbitmark.librm.bookmark import Bookmark

class BookmarkTableModel(QAbstractTableModel):
    "Handles the display of the main table of bookmarks."
    dataChanged = pyqtSignal()

    @unique
    class ModelColumn(Enum):
        """
        Heavy Enum representing the columns in this model. The goal is to
        factor the complexity out of the overridden model methods.
        """
        Name = 0
        Tags = 1

        def __str__(self) -> str:  # pylint: disable=invalid-str-returned
            return self.name

        def data(self, bookmark):
            """
            Given a Bookmark object,
            return the data from it that this column should contain.
            """
            # false positive
            # pylint: disable=comparison-with-callable
            if self.name == 'Name':
                return bookmark.name
            elif self.name == 'Tags':
                return ', '.join(i.text for i in bookmark.tags)
            raise AssertionError("Model column %i not defined in data()"
                                 % self.value)

        #pylint: disable=superfluous-parens
        def sort_function(self) -> Callable[[Bookmark], Any]:
            "Return a key function that will sort this column correctly."
            # false positive
            # pylint: disable=comparison-with-callable
            if self.name == 'Name':
                return (lambda i: i.name)
            elif self.name == 'Tags':
                print("DEBUG: Sorting by this column is not supported.")
                return (lambda i: None)
            else:
                raise AssertionError(
                    "Model column %i not defined in sort_function()"
                    % self.value)


    def __init__(self, parent) -> None:
        QAbstractTableModel.__init__(self)
        self.parent = parent
        self.headerdata = ("Name", "Tags")
        self.L: List[Bookmark] = []  # pylint: disable=invalid-name

    ### Standard reimplemented methods ###
    def rowCount(self, parent) -> int: #pylint: disable=no-self-use,unused-argument
        return len(self.L)
    def columnCount(self, parent) -> int: #pylint: disable=no-self-use,unused-argument
        return len(self.headerdata)

    def flags(self, index) -> Any: #pylint: disable=no-self-use,unused-argument
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, col, orientation, role) -> Optional[str]:
        "Return headers for the model table."
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headerdata[col]
        else:
            return None

    def data(self, index, role):
        "Return data for a given row and column."
        if not index.isValid():
            return None
        if not role in (Qt.DisplayRole, Qt.EditRole):
            return None

        col = self.ModelColumn(index.column())
        mark = self.L[index.row()]
        return col.data(mark)

    def sort(self, col, order=Qt.AscendingOrder):
        "Re-sort the model data by the given column and ordering."
        rev = (order != Qt.AscendingOrder)
        self.beginResetModel()
        self.L.sort(key=self.ModelColumn(col).sort_function(), reverse=rev)
        self.endResetModel()


    ### Custom methods ###
    def indexFromPk(self, pk):
        "Return the model index of a given primary key."
        for row, obj in enumerate(self.L):
            if obj.id == pk:
                return self.index(row, 0)
        return None

    def updateContents(self, marks) -> None:
        """
        Replace the current set of bookmarks held by the model with /marks/,
        for instance when the filter is changed.
        """
        self.beginResetModel()
        self.L = marks
        self.sort(0)
        self.dataChanged.emit()
        self.endResetModel()

    def nextAfterDelete(self, index):
        """
        Return the index of the item that should be selected after deleting the
        item at /index/.
        """
        row = index.row()
        try:
            if (row - 1) >= 0:
                nextObj = self.L[row-1]
            else:
                # index was negative, this is the top entry; go below
                nextObj = self.L[row+1]
        except IndexError:
            # there are no other items
            return None
        else:
            return self.indexFromPk(nextObj.id)

    def updateAfterDelete(self, index) -> None:
        """
        Update the model to show that the item at /index/ has been deleted
        from the database.
        """
        self.beginResetModel()
        del self.L[index.row()]
        self.endResetModel()

    def getObj(self, index):
        "Return an object from the list by its model index."
        try:
            return self.L[index.row()]
        except IndexError:
            return None
