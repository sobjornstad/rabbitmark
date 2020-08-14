"""
main.py -- RabbitMark Qt application
"""

# RabbitMark
# Copyright (c) 2015, 2018, 2019, 2020 Soren Bjornstad.
# All rights reserved (temporary; if you read this and want such, contact me
# for relicensing under some FOSS license).

import re
import sys
from typing import Any, Dict, NoReturn

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QShortcut, QMessageBox
from PyQt5.QtGui import QDesktopServices, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QUrl
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SessionType

from .bookmark_table import BookmarkTableModel
from .forms.main import Ui_MainWindow
from .librm import bookmark
from .librm import tag as tag_ops
from .librm.models import Base
from . import utils
from . import wayback_search_dialog


class MainWindow(QMainWindow):
    "RabbitMark application window."
    def __init__(self) -> None:
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
        sf.actionCopyUrl.triggered.connect(self.copyUrl)
        sf.actionBrowseToUrl.triggered.connect(self.openUrl)

        sf.actionRenameTag.triggered.connect(self.onRenameTag)
        sf.actionDeleteTag.triggered.connect(self.onDeleteTag)
        sf.actionMergeTag.triggered.connect(self.onMergeTag)
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

    def _currentSearchMode(self) -> utils.SearchMode:
        return utils.SearchMode(self.form.tagsModeDropdown.currentIndex())

    #pylint: disable=unused-argument
    def closeEvent(self, evt) -> NoReturn:
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self) -> NoReturn:
        "Clean up and quit RabbitMark."
        # fake changing focus: the widget name for new is arbitrary,
        # one of the editable boxes is required for old
        self.maybeSaveBookmark(old=self.form.nameBox, new=self.form.nameBox)
        # false positive
        # pylint: disable=no-member
        self.session.commit()
        self.session.close()
        sys.exit(0)

    def onTogglePrivate(self) -> None:
        self.showPrivates = not self.showPrivates
        self.doUpdateForSearch()

    def onAddBookmarkFromClipboard(self) -> None:
        "Create a new bookmark from the URL on the clipboard."
        pastedUrl = str(QApplication.clipboard().text()).strip()
        if '://' not in pastedUrl:
            utils.warningBox("No protocol (e.g., http://) in URL. Adding "
                             "http:// to beginning. You may wish to check "
                             "the URL.", "URL possibly invalid")
            pastedUrl = 'http://' + pastedUrl
        self._newBookmark(pastedUrl)

    def onAddBookmark(self) -> None:
        "Create a new bookmark without a given URL."
        self._newBookmark("http://")

    def _newBookmark(self, url) -> None:
        "Common portion of creating a new bookmark."
        # Create the new item with any tags that are selected.
        tags = [str(i.text())
                for i in self.form.tagList.selectedItems()
                if str(i.text()) != utils.NOTAGS]

        # Full-text filter is automatically cleared on add -- otherwise, the new
        # item won't be visible!
        self.form.searchBox.setText("")
        self.doUpdateForSearch()
        # If in AND mode, turn off "no tags" mode, or it similarly won't be visible.
        if self._currentSearchMode() == utils.SearchMode.And:
            self.form.tagList.item(0).setSelected(False)

        newBookmark = bookmark.add_bookmark(self.session, url, tags)
        self.session.commit()  # pylint: disable=no-member

        self.doUpdateForSearch()
        index = self.tableModel.indexFromPk(newBookmark.id)
        if index is not None:
            self.tableView.setCurrentIndex(index)
            self.form.nameBox.setFocus()

    def deleteCurrent(self) -> None:
        "Delete the selected bookmark."
        if not self.sm.hasSelection():
            utils.errorBox("Please select a bookmark to delete.",
                           "No bookmark selected")
            return
        curIndex = self.tableView.currentIndex()
        nextRow = self.tableModel.nextAfterDelete(curIndex)

        mark = self.tableModel.getObj(curIndex)
        bookmark.delete_bookmark(self.session, mark)
        self.session.commit()  # pylint: disable=no-member

        self.tableModel.updateAfterDelete(curIndex)
        self.resetTagList()
        self.tableView.setCurrentIndex(nextRow)

    def copyUrl(self) -> None:
        QApplication.clipboard().setText(self.form.urlBox.text())
    def openUrl(self) -> None:
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def onWayBackMachine(self) -> None:
        "Find a snapshot of the item's URL in the WayBackMachine."
        mark = self.tableModel.getObj(self.tableView.currentIndex())

        if re.match("https?://web.archive.org/", mark.url):
            if utils.questionBox(
                    "This bookmark appears to already be pointing at a snapshot in "
                    "the WayBackMachine. Would you like to pick a new snapshot?",
                    "Select new snapshot?") == QMessageBox.Yes:
                url = re.sub("https?://web.archive.org/web/[0-9]+/(.*)", r"\1",
                             mark.url)
            else:
                return
        else:
            url = mark.url

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        archiveUrl = wayback_search_dialog.way_back_from_url(self, url)
        if archiveUrl is not None:
            self.form.urlBox.setText(archiveUrl)

    def onRenameTag(self) -> None:
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
                self.session.commit()  # pylint: disable=no-member
                self.resetTagList()
                self.fillEditPane()
            else:
                utils.errorBox("A tag by that name already exists.",
                               "Cannot rename tag")
        self.form.tagList.findItems(new, Qt.MatchExactly)[0].setSelected(True)

    def onDeleteTag(self) -> None:
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
            self.session.commit()  # pylint: disable=no-member
            self.resetTagList()
            self.fillEditPane()

    def onMergeTag(self) -> None:
        "Merge the selected tag into another."
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
        new, doContinue = utils.inputBox(f"Merge tag {tag} into:", "Merge tag")
        if doContinue:
            if tag_ops.merge_tags(self.session, tag, new):
                self.session.commit()  # pylint: disable=no-member
                self.resetTagList()
                self.fillEditPane()
            self.form.tagList.findItems(new, Qt.MatchExactly)[0].setSelected(True)

    def resetTagList(self) -> None:
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

    def maybeSaveBookmark(self, old, new) -> None:
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
                self.session.commit()  # pylint: disable=no-member
                self.resetTagList()
            self.doUpdateForSearch()

    def doUpdateForSearch(self) -> None:
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
        searchMode = self._currentSearchMode()

        nameText = "%" + self.form.searchBox.text() + "%"
        marks = bookmark.find_bookmarks(self.session, nameText, selectedTags,
                                        self.showPrivates, searchMode)
        self.tableModel.updateContents(marks)
        self.reselectItem(oldId)
        self.updateTitleCount(self.tableModel.rowCount(self))

    def reselectItem(self, item=None) -> None:
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

    def fillEditPane(self) -> None:
        "Fill the editor/details pane with data from the currently selected bookmark."
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

    def tagsSelect(self, what) -> None:
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

    def mRepr(self) -> Dict[str, Any]:
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

    def updateTitleCount(self, count) -> None:
        """
        Change the count of matching items that appears in the title bar to
        /count/.
        """
        self.setWindowTitle("RabbitMark - %i match%s" % (
            count, '' if count == 1 else 'es'))


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

def startQt() -> None:
    "Application entry point."
    app = QApplication(sys.argv)
    mw = MainWindow()
    app.focusChanged.connect(mw.maybeSaveBookmark)
    mw.show()
    app.exec_()

if __name__ == '__main__':
    startQt()
