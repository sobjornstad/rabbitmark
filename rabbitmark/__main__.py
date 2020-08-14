"""
main.py -- RabbitMark Qt application
"""

# RabbitMark
# Copyright (c) 2015, 2018, 2019, 2020 Soren Bjornstad.
# All rights reserved (temporary; if you read this and want such, contact me
# for relicensing under some FOSS license).

from enum import Enum, unique
import sys

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QShortcut, QMessageBox
from PyQt5.QtGui import QDesktopServices, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QAbstractTableModel, QUrl, pyqtSignal
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .forms.main import Ui_MainWindow
from .librm import bookmark
from .librm import tag as tag_ops
from .librm.models import Tag, Base
from . import utils
from . import wayback_search_dialog


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

    def deleteBookmark(self, index):
        """
        Delete the bookmark at /index/ in the table. Return the index of the
        entry to select after deletion, or None if this is the only entry.
        """
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

        sess = self.parent.Session()
        bookmark.delete_bookmark(sess, mark)
        sess.commit()

        self.beginResetModel()
        del self.L[row]
        self.endResetModel()
        return self.indexFromPk(nextObj.id)

    def getObj(self, index):
        "Return an object from the list by its model index."
        try:
            return self.L[index.row()]
        except IndexError:
            return None


class MainWindow(QMainWindow):
    "RabbitMark application window."
    def __init__(self):
        QMainWindow.__init__(self)
        self.form = Ui_MainWindow()
        self.form.setupUi(self)

        self.Session = make_Session()
        self.session = self.Session()

        # set up actions
        sf = self.form
        sf.action_Quit.triggered.connect(self.quit)
        sf.actionDelete.triggered.connect(self.deleteCurrent)
        sf.actionNew.triggered.connect(self.onAddBookmark)
        sf.actionNew_from_clipboard.triggered.connect(
            self.onAddBookmarkFromClipboard)
        sf.actionRenameTag.triggered.connect(self.onRenameTag)
        sf.actionDeleteTag.triggered.connect(self.onDeleteTag)
        sf.actionWayBack.triggered.connect(self.onWayBackMachine)
        sf.actionShowPrivate.triggered.connect(self.onTogglePrivate)
        self.showPrivates = False

        sf.tagsAllButton.clicked.connect(lambda: self.tagsSelect('all'))
        sf.tagsNoneButton.clicked.connect(lambda: self.tagsSelect('none'))
        sf.tagsInvertButton.clicked.connect(lambda: self.tagsSelect('invert'))
        sf.copyUrlButton.clicked.connect(self.copyUrl)
        sf.browseUrlButton.clicked.connect(self.openUrl)
        findShortcut = QShortcut(QKeySequence("Ctrl+F"), sf.searchBox)
        findShortcut.activated.connect(sf.searchBox.setFocus)

        # Set up tag mode dropdown.
        # Indexes of these options should match with utils.SearchMode.
        sf.tagsModeDropdown.addItem("Require at least one selected tag (OR)")
        sf.tagsModeDropdown.addItem("Require all selected tags (AND)")
        sf.tagsModeDropdown.activated.connect(self.doUpdateForSearch)

        # set up data table
        self.tableView = self.form.bookmarkTable
        self.tableModel = BookmarkTableModel(self)
        self.tableView.setModel(self.tableModel)
        self.sm = self.tableView.selectionModel()
        self.sm.selectionChanged.connect(self.fillEditPane)

        # set up tag list
        self.tags = tag_ops.scan_tags(self.session)
        for i in self.tags:
            self.form.tagList.addItem(i)
        self.form.tagList.sortItems()

        # set up re-search triggers and update for the first time
        self.form.searchBox.textChanged.connect(self.doUpdateForSearch)
        self.form.tagList.itemSelectionChanged.connect(self.doUpdateForSearch)
        self.doUpdateForSearch()

    #pylint: disable=unused-argument
    def closeEvent(self, evt):
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self):
        "Clean up and quit RabbitMark."
        # fake changing focus: the widget name for new is arbitrary,
        # one of the editable boxes is required for old
        self.maybeSaveBookmark(old=self.form.nameBox, new=self.form.nameBox)
        self.session.commit()
        self.session.close()
        sys.exit(0)

    def onTogglePrivate(self):
        self.showPrivates = not self.showPrivates
        self.doUpdateForSearch()

    def onAddBookmarkFromClipboard(self):
        "Create a new bookmark from the URL on the clipboard."
        pastedUrl = str(QApplication.clipboard().text()).strip()
        if '://' not in pastedUrl:
            utils.warningBox("No protocol (e.g., http://) in URL. Adding "
                             "http:// to beginning. You may wish to check "
                             "the URL.", "URL possibly invalid")
            pastedUrl = 'http://' + pastedUrl
        self._newBookmark(pastedUrl)

    def onAddBookmark(self):
        "Create a new bookmark without a given URL."
        self._newBookmark("http://")

    def _newBookmark(self, url):
        tags = [str(i.text())
                for i in self.form.tagList.selectedItems()]
        newBookmark = bookmark.add_bookmark(self.session, url, tags)
        self.session.commit()

        self.doUpdateForSearch()
        index = self.tableModel.indexFromPk(newBookmark.id)
        self.tableView.setCurrentIndex(index)
        self.form.nameBox.setFocus()

    def deleteCurrent(self):
        "Delete the selected bookmark."
        if not self.sm.hasSelection():
            utils.errorBox("Please select a bookmark to delete.",
                           "No bookmark selected")
            return
        curIndex = self.tableView.currentIndex()
        newIndex = self.tableModel.deleteBookmark(curIndex)
        self.resetTagList()
        self.tableView.setCurrentIndex(newIndex)

    def copyUrl(self):
        QApplication.clipboard().setText(self.form.urlBox.text())
    def openUrl(self):
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def onWayBackMachine(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        archiveUrl = wayback_search_dialog.way_back_from_url(self, mark.url)
        if archiveUrl is not None:
            self.form.urlBox.setText(archiveUrl)

    def onRenameTag(self):
        "Rename the selected tag."
        tags = [str(i.text())
                for i in self.form.tagList.selectedItems()]

        if len(tags) < 1:
            utils.errorBox("Please select a tag to rename.",
                           "No tag selected")
            return
        elif len(tags) > 1:
            utils.errorBox("Tags cannot be renamed in bulk. Please select"
                           "exactly one tag.", "Cannot rename multiple tags")
            return

        tag = tags[0]
        new, doContinue = utils.inputBox("New name for tag:",
                                         "Rename tag", tag)
        if doContinue:
            if tag_ops.rename_tag(self.session, tag, new):
                self.resetTagList()
                self.fillEditPane()
            else:
                utils.errorBox("A tag by that name already exists.",
                               "Cannot rename tag")

    def onDeleteTag(self):
        "Delete the selected tag."
        tags = [str(i.text())
                for i in self.form.tagList.selectedItems()]

        if len(tags) < 1:
            utils.errorBox("Please select a tag to delete.",
                           "No tag selected")
            return
        elif len(tags) > 1:
            utils.errorBox("Sorry, you currently cannot delete tags in bulk.",
                           "Cannot delete multiple tags")
            return

        tag = tags[0]
        if tag == utils.NOTAGS:
            utils.errorBox("You cannot delete '%s'. It is not a tag; rather, "
                           "it indicates that you would like to search for "
                           "items that do not have any tags." % utils.NOTAGS,
                           "Not deleteable")
            return

        r = utils.questionBox("This will permanently delete the tag '%s' from "
                              "all of your bookmarks. Are you sure you want "
                              "to continue?" % tag, "Delete tag?")
        if r == QMessageBox.Yes:
            tag_ops.delete_tag(self.session, tag)
            self.resetTagList()
            self.fillEditPane()

    def resetTagList(self):
        """
        Update the tag list widget to match the current state of the db.
        """
        # Get updated tag list.
        self.tags = tag_ops.scan_tags(self.session)

        # Remove tags that no longer exist.
        toRemove = [self.form.tagList.item(i)
                    for i in range(self.form.tagList.count())
                    if self.form.tagList.item(i).text() not in self.tags]
        for i in toRemove:
            self.form.tagList.takeItem(self.form.tagList.row(i))

        # Add new tags and resort list.
        for i in self.tags:
            if not self.form.tagList.findItems(i, Qt.MatchExactly):
                self.form.tagList.addItem(i)
        self.form.tagList.sortItems()

    def maybeSaveBookmark(self, old, new):
        """
        Update the state of the database object associated with the currently
        selected bookmark.

        Arguments:
            old - the widget that previously had focus
            new - the widget that has just gained focus (unused)

        Return:
            None.

        This method is called by the signal set in startQt() when any focus
        changes, as well as before quitting.
        """
        sf = self.form
        if old in (sf.nameBox, sf.urlBox, sf.descriptionBox, sf.tagsBox,
                   sf.privateCheck):
            mark = self.tableModel.getObj(self.tableView.currentIndex())
            QApplication.processEvents()
            if mark is None:
                return # nothing is selected
            if bookmark.save_if_edited(self.session, mark, self.mRepr()):
                self.resetTagList()
                self.session.commit()
            self.doUpdateForSearch()

    def doUpdateForSearch(self):
        """
        Call tableModel.updateForSearch() to bring the contents of the
        bookmarks table into sync with the filter and tag selection.

        We determine and pass the text in the filter box and a list of the tags
        selected, and we restore the selection to the currently selected
        bookmark after the view is refreshed if that bookmark is still in the
        new view.

        No arguments, no return.
        """
        selectedTags = [str(i.text())
                        for i in self.form.tagList.selectedItems()]
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        oldId = None if mark is None else mark.id
        searchMode = utils.SearchMode(
            self.form.tagsModeDropdown.currentIndex())


        nameText = "%" + self.form.searchBox.text() + "%"
        marks = bookmark.find_bookmarks(self.session, nameText, selectedTags,
                                        self.showPrivates, searchMode)
        self.tableModel.updateContents(marks)
        self.reselectItem(oldId)
        self.updateTitleCount(self.tableModel.rowCount(self))

    def reselectItem(self, item=None):
        """
        Select the given /item/ if it still exists in the view, or the first
        item in the view if it doesn't or /item/ is None.

        This method should to be called after updating the table view using a
        resetModel() command, as that causes the loss of the current selection.

        Arguments:
            item (default None) - if not None, attempt to select the item by
                this primary key.
        """
        if item is None:
            idx = self.tableModel.index(0, 0)
        else:
            idx = self.tableModel.indexFromPk(item)
            if idx is None: # provided item isn't in this view
                idx = self.tableModel.index(0, 0)

        self.tableView.setCurrentIndex(idx)
        self.fillEditPane()

    def fillEditPane(self):
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        if not self.sm.selectedRows():
            # nothing selected; hide editor pane
            self.form.splitter.widget(1).setVisible(False)
        else:
            self.form.splitter.widget(1).setVisible(True)
            self.form.nameBox.setText(mark.name)
            self.form.urlBox.setText(mark.url)
            self.form.descriptionBox.setPlainText(mark.description)
            self.form.privateCheck.setChecked(mark.private)
            tags = ', '.join([i.text for i in mark.tags])
            self.form.tagsBox.setText(tags)
            # If a name or URL is too long to fit in the box, this will make
            # the box show the beginning of it rather than the end.
            for i in (self.form.nameBox, self.form.urlBox, self.form.tagsBox):
                i.setCursorPosition(0)

    def tagsSelect(self, what):
        "Select tags en masse using the convenience buttons at the bottom."
        # Block signals so that we only have to call itemSelectionChanged
        # once instead of numTags times -- this *greatly* improves performance.
        oldSigs = self.form.tagList.blockSignals(True)
        for i in range(self.form.tagList.count()):
            if what == 'none':
                self.form.tagList.item(i).setSelected(False)
            elif what == 'all':
                self.form.tagList.item(i).setSelected(True)
            elif what == 'invert':
                currentStatus = self.form.tagList.item(i).isSelected()
                self.form.tagList.item(i).setSelected(not currentStatus)
            else:
                assert False, "Invalid argument to tagsSelect!"
        self.form.tagList.blockSignals(oldSigs)
        self.form.tagList.itemSelectionChanged.emit()

    def mRepr(self):
        """
        Short for "mark representation": return a dictionary of the content
        currently in the fields so that the model can compare and/or save it.
        """
        return {
            'name': str(self.form.nameBox.text()),
            'url': str(self.form.urlBox.text()),
            'description': str(self.form.descriptionBox.toPlainText()),
            'private': self.form.privateCheck.isChecked(),
            'tags': [i.strip() for i in
                     str(self.form.tagsBox.text()).split(',')
                     if i.strip() != ''],
        }

    def updateTitleCount(self, count):
        """
        Change the count of matching items that appears in the title bar to
        /count/.
        """
        self.setWindowTitle("RabbitMark - %i match%s" % (
            count, '' if count == 1 else 'es'))


def make_Session():
    "Create a SQLAlchemy Session object, from which sessions can be spawned."
    engine = create_engine('sqlite:///sorenmarks-test.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine) # will not recreate existing tables/dbs
    return Session

# http://stackoverflow.com/questions/9671490/
# how-to-set-sqlite-pragma-statements-with-sqlalchemy
#pylint: disable=unused-argument
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    "Set SQLite pragma options for RabbitMark execution."
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

def startQt():
    "Application entry point."
    app = QApplication(sys.argv)
    mw = MainWindow()
    app.focusChanged.connect(mw.maybeSaveBookmark)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    startQt()
