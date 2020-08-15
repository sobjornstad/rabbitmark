"""
main_window.py -- RabbitMark Qt application, application window
"""

import sys
from typing import NoReturn, Optional

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut
from PyQt5.QtGui import QDesktopServices, QKeySequence
from PyQt5.QtCore import Qt, QUrl

from .bookmark_table import BookmarkTableModel
from .forms.main import Ui_MainWindow
from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from .librm import bookmark
from .librm import tag as tag_ops
from . import utils
from . import wayback_search_dialog
from . import link_check_dialog


class MainWindow(QMainWindow):
    "RabbitMark application window."
    def __init__(self, sessionmaker) -> None:
        QMainWindow.__init__(self)
        self.form = Ui_MainWindow()
        self.form.setupUi(self)
        self.Session = sessionmaker
        self.session = self.Session()

        # set up actions
        sf = self.form
        sf.action_Quit.triggered.connect(self.quit)
        sf.actionDelete.triggered.connect(self.onDeleteBookmark)
        sf.actionNew.triggered.connect(self.onAddBookmark)
        sf.actionNew_from_clipboard.triggered.connect(
            self.onAddBookmarkFromClipboard)
        sf.actionCopyUrl.triggered.connect(self.onCopyUrl)
        sf.actionBrowseToUrl.triggered.connect(self.onBrowseForUrl)

        sf.actionRenameTag.triggered.connect(self.onRenameTag)
        sf.actionDeleteTag.triggered.connect(self.onDeleteTag)
        sf.actionMergeTag.triggered.connect(self.onMergeTag)
        sf.actionWayBack.triggered.connect(self.onWayBackMachine)
        sf.actionShowPrivate.triggered.connect(self.onTogglePrivate)
        sf.actionBrokenLinks.triggered.connect(self.onCheckBrokenLinks)
        self.showPrivates = False

        sf.tagsAllButton.clicked.connect(lambda: self.tagsSelect('all'))
        sf.tagsNoneButton.clicked.connect(lambda: self.tagsSelect('none'))
        sf.tagsInvertButton.clicked.connect(lambda: self.tagsSelect('invert'))

        findShortcut = QShortcut(QKeySequence("Ctrl+F"), sf.searchBox)
        findShortcut.activated.connect(self.onFocusFind)

        # Set up tag mode dropdown.
        # Indexes of these options should match with utils.SearchMode.
        sf.tagsModeDropdown.addItem("Require at least one selected tag (OR)")
        sf.tagsModeDropdown.addItem("Require all selected tags (AND)")
        sf.tagsModeDropdown.activated.connect(self._updateForSearch)

        # set up data table
        self.tableView = self.form.bookmarkTable
        self.tableModel = BookmarkTableModel(self)
        self.tableView.setModel(self.tableModel)
        self.sm = self.tableView.selectionModel()
        self.sm.selectionChanged.connect(self.fillEditPane)

        # set up tag list
        self.tags = tag_ops.scan_tags(self.session, self.showPrivates)
        for i in self.tags:
            self.form.tagList.addItem(i)
        self.form.tagList.sortItems()

        # set up details form
        self.detailsForm = BookmarkDetailsWidget()
        self.detailsForm.setupUi(self.form.detailsWidget)
        self.detailsForm.copyUrlButton.clicked.connect(self.onCopyUrl)
        self.detailsForm.browseUrlButton.clicked.connect(self.onBrowseForUrl)

        # set up re-search triggers and update for the first time
        self.form.searchBox.textChanged.connect(self._updateForSearch)
        self.form.tagList.itemSelectionChanged.connect(self._updateForSearch)
        self._updateForSearch()


    ### Helper methods ###
    def _currentSearchMode(self) -> utils.SearchMode:
        return utils.SearchMode(self.form.tagsModeDropdown.currentIndex())

    def _getSingleTagName(self) -> Optional[str]:
        """
        Return the name of the single tag currently selected, or display an error
        message and return None if there is not exactly one tag selected.
        """
        tags = [str(i.text())
                for i in self.form.tagList.selectedItems()]

        if len(tags) < 1:
            utils.errorBox("Please select a tag.", "No tag selected")
            return None
        elif len(tags) > 1:
            utils.errorBox(
                "Tags cannot be edited in bulk. Please select exactly one tag.",
                "Cannot rename multiple tags")
            return None
        elif tags[0] == utils.NOTAGS:
            utils.errorBox(
                f"You cannot edit '{utils.NOTAGS}'. It is not a tag; rather, "
                f"it indicates that you would like to search for items that do not "
                f"have any tags.",
                "Item not editable")
            return None

        return tags[0]

    def _newBookmark(self, url) -> None:
        "Common portion of creating a new bookmark."
        # Create the new item with any tags that are selected.
        tags = [str(i.text())
                for i in self.form.tagList.selectedItems()
                if str(i.text()) != utils.NOTAGS]

        # Full-text filter is automatically cleared on add -- otherwise, the new
        # item won't be visible!
        self.form.searchBox.setText("")
        self._updateForSearch()
        # If in AND mode, turn off "no tags" mode, or it similarly won't be visible.
        if self._currentSearchMode() == utils.SearchMode.And:
            self.form.tagList.item(0).setSelected(False)

        newBookmark = bookmark.add_bookmark(self.session, url, tags)
        self.session.commit()  # pylint: disable=no-member

        self._updateForSearch()
        index = self.tableModel.indexFromPk(newBookmark.id)
        if index is not None:
            self.tableView.setCurrentIndex(index)
            self.detailsForm.nameBox.selectAll()
            self.detailsForm.nameBox.setFocus()

    def _reselectItem(self, item=None) -> None:
        """
        Select the given /item/ if it still exists in the view, or the first
        item in the view if it doesn't or /item/ is None.

        This method should be called after updating the table view using a
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

    def _resetTagList(self) -> None:
        """
        Update the tag list widget to match the current state of the database.
        Need to call after anything that might add or remove tags.
        """
        # Get updated tag list.
        self.tags = tag_ops.scan_tags(self.session, self.showPrivates)

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

    def _updateTitleCount(self, count) -> None:
        """
        Change the count of matching items that appears in the title bar to
        /count/.
        """
        self.setWindowTitle("RabbitMark - %i match%s" % (
            count, '' if count == 1 else 'es'))

    def _updateForSearch(self) -> None:
        """
        Update the bookmarks table to match the filter and tag selection.

        We determine and pass the text in the filter box and a list of the tags
        selected, and we restore the selection to the currently selected
        bookmark after the view is refreshed if that bookmark is still in the
        new view.
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
        self._reselectItem(oldId)
        self._updateTitleCount(self.tableModel.rowCount(self))


    ### Evil in-betweens. Called from events and from other methods. ###
    def fillEditPane(self) -> None:
        "Fill the editor/details pane with data from the currently selected bookmark."
        sfdw = self.detailsForm
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        if not self.sm.selectedRows():
            # nothing selected; hide editor pane
            self.form.splitter.widget(1).setVisible(False)
        else:
            self.form.splitter.widget(1).setVisible(True)
            sfdw.nameBox.setText(mark.name)
            sfdw.urlBox.setText(mark.url)
            sfdw.descriptionBox.setPlainText(mark.description)
            sfdw.privateCheck.setChecked(mark.private)
            sfdw.linkcheckCheck.setChecked(mark.skip_linkcheck)
            tags = ', '.join([i.text for i in mark.tags])
            sfdw.tagsBox.setText(tags)
            # If a name or URL is too long to fit in the box, this will make
            # the box show the beginning of it rather than the end.
            for i in (sfdw.nameBox, sfdw.urlBox, sfdw.tagsBox):
                i.setCursorPosition(0)

    def maybeSaveBookmark(self, old, new) -> None:  # pylint: disable=unused-argument
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
        sfdw = self.detailsForm
        if old in (sfdw.nameBox, sfdw.urlBox, sfdw.descriptionBox, sfdw.tagsBox,
                   sfdw.privateCheck, sfdw.linkcheckCheck):
            mark = self.tableModel.getObj(self.tableView.currentIndex())
            QApplication.processEvents()
            if mark is None:
                return # nothing is selected
            if bookmark.save_if_edited(self.session, mark, utils.mark_dictionary(sfdw)):
                self.session.commit()  # pylint: disable=no-member
                self._resetTagList()
            self._updateForSearch()

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


    ### Event handlers ###
    # Bookmarks
    def onAddBookmark(self) -> None:
        "Create a new bookmark without a given URL."
        self._newBookmark("http://")

    def onAddBookmarkFromClipboard(self) -> None:
        "Create a new bookmark from the URL on the clipboard."
        pastedUrl = str(QApplication.clipboard().text()).strip()
        if '://' not in pastedUrl:
            utils.warningBox("No protocol (e.g., http://) in URL. Adding "
                             "http:// to beginning. You may wish to check "
                             "the URL.", "URL possibly invalid")
            pastedUrl = 'http://' + pastedUrl
        self._newBookmark(pastedUrl)

    def onBrowseForUrl(self) -> None:
        QDesktopServices.openUrl(QUrl(self.detailsForm.urlBox.text()))

    def onCopyUrl(self) -> None:
        QApplication.clipboard().setText(self.detailsForm.urlBox.text())

    def onDeleteBookmark(self) -> None:
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
        self._resetTagList()
        self.tableView.setCurrentIndex(nextRow)

    def onWayBackMachine(self) -> None:
        "Find a snapshot of the item's URL in the WayBackMachine."
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        archiveUrl = wayback_search_dialog.init_wayback_search(self, mark.url)
        if archiveUrl is not None:
            self.detailsForm.urlBox.setText(archiveUrl)
            self.maybeSaveBookmark(self.detailsForm.urlBox, None)

    # Tags
    def onDeleteTag(self) -> None:
        "Delete the selected tag."
        tag = self._getSingleTagName()
        if tag is None:
            return

        if utils.questionBox(f"This will permanently delete the tag '{tag}' "
                             f"from all of your bookmarks. "
                             f"Are you sure you want to continue?",
                             "Delete tag?"):
            tag_ops.delete_tag(self.session, tag)
            self.session.commit()  # pylint: disable=no-member
            self._resetTagList()
            self.fillEditPane()

    def onMergeTag(self) -> None:
        "Merge the selected tag into another."
        tag = self._getSingleTagName()
        if tag is None:
            return

        new, doContinue = utils.inputBox(f"Merge tag '{tag}' into:", "Merge tag")
        if doContinue:
            if tag_ops.merge_tags(self.session, tag, new):
                self.session.commit()  # pylint: disable=no-member
                self._resetTagList()
                self.fillEditPane()
            # select the tag we merged into
            self.form.tagList.findItems(new, Qt.MatchExactly)[0].setSelected(True)

    def onRenameTag(self) -> None:
        "Rename the selected tag."
        tag = self._getSingleTagName()
        if tag is None:
            return

        new, doContinue = utils.inputBox("New name for tag:", "Rename tag", tag)
        if doContinue:
            if tag_ops.rename_tag(self.session, tag, new):
                self.session.commit()  # pylint: disable=no-member
                self._resetTagList()
                self.fillEditPane()
            else:
                utils.errorBox("A tag by that name already exists.",
                               "Cannot rename tag")

            # select the newly renamed tag
            self.form.tagList.findItems(new, Qt.MatchExactly)[0].setSelected(True)

    # Entire view
    def onFocusFind(self) -> None:
        self.form.searchBox.selectAll()
        self.form.searchBox.setFocus()

    def onCheckBrokenLinks(self) -> None:
        "Scan the database for broken links and help the user correct them."
        obtain_dlg = link_check_dialog.LinkCheckProgressDialog(self, self.Session)
        obtain_dlg.start()
        obtain_dlg.exec_()
        blinks = obtain_dlg.blinks

        if blinks:
            fix_dlg = link_check_dialog.LinkCheckDialog(self, blinks, self.session)
            fix_dlg.exec_()

            # Since we could have edited things within the dialog, we need to resync.
            self._updateForSearch()
            self._resetTagList()

    def onTogglePrivate(self) -> None:
        """
        Choose whether to hide or show private bookmarks and tags. A tag is
        considered private if it has no member bookmarks which are not private.
        """
        self.showPrivates = not self.showPrivates
        self._updateForSearch()
        self._resetTagList()

    # Named by convention.
    #pylint: disable=unused-argument
    def closeEvent(self, evt) -> NoReturn:
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self) -> NoReturn:
        "Clean up and quit RabbitMark."
        # fake changing focus: the widget name for new is arbitrary,
        # one of the editable boxes is required for old
        self.maybeSaveBookmark(old=self.detailsForm.nameBox,
                               new=self.detailsForm.nameBox)
        # Double-check we don't have any uncommitted changes.
        # false positive
        # pylint: disable=no-member
        self.session.commit()
        self.session.close()
        sys.exit(0)


def start(sessionmaker) -> None:
    "Application entry point."
    app = QApplication(sys.argv)
    mw = MainWindow(sessionmaker)
    app.focusChanged.connect(mw.maybeSaveBookmark)
    mw.show()
    app.exec_()
