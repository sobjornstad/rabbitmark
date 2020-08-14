from enum import Enum, unique

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QAbstractTableModel, pyqtSignal

class BookmarkTableModel(QAbstractTableModel):
    """
    Handles the interface to the database. Currently it *also* handles tag
    management, which isn't really part of the description of the model; this
    code should be moved into a TagManager or a set of functions of that
    description soon.
    """
    dataChanged = pyqtSignal()

    @unique
    class ModelColumn(Enum):
        """
        Heavy Enum representing the columns in this model. The goal is to
        factor the complexity out of the overridden model methods.
        """
        Name = 0
        Tags = 1

        def __str__(self):
            return self.name

        def data(self, bookmark):
            """
            Given a Bookmark object,
            return the data from it that this column should contain.
            """
            if self.name == 'Name':
                return bookmark.name
            elif self.name == 'Tags':
                return ', '.join(i.text for i in bookmark.tags)
            raise AssertionError("Model column %i not defined in data()"
                                 % self.value)

        #pylint: disable=superfluous-parens
        def sort_function(self):
            "Return a key function that will sort this column correctly."
            if self.name == 'Name':
                return (lambda i: i.name)
            elif self.name == 'Tags':
                print("DEBUG: Sorting by this column is not supported.")
                return (lambda i: None)
            else:
                raise AssertionError(
                    "Model column %i not defined in sort_function()"
                    % self.value)


    def __init__(self, parent):
        QAbstractTableModel.__init__(self)
        self.parent = parent
        self.headerdata = ("Name", "Tags")
        self.L = []

    ### Standard reimplemented methods ###
    def rowCount(self, parent): #pylint: disable=no-self-use,unused-argument
        return len(self.L)
    def columnCount(self, parent): #pylint: disable=no-self-use,unused-argument
        return len(self.headerdata)

    def flags(self, index): #pylint: disable=no-self-use,unused-argument
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, col, orientation, role):
        "Return headers for the model table."
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headerdata[col]
        else:
            return None

    def data(self, index, role):
        "Return data for a given row and column."
        if not index.isValid():
            return None
        if not (role == Qt.DisplayRole or role == Qt.EditRole):
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

    def updateContents(self, marks):
        self.beginResetModel()
        self.L = marks
        self.sort(0)
        self.dataChanged.emit()
        self.endResetModel()

    def nextAfterDelete(self, index):
        row = index.row()
        mark = self.L[row]
        try:
            if (row - 1) >= 0:
                nextObj = self.L[row-1]
            else:
                # index was negative, this is the top entry; go below
                nextObj = self.L[row+1]
        except IndexError:
            # there are no other items
            nextObj = None
        return self.indexFromPk(nextObj.id)

    def updateAfterDelete(self, index) -> None:
        """
        Call after deleting the bookmark at /row/ in the table.
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