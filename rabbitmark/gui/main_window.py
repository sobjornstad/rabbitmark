"""
main_window.py -- RabbitMark Qt application, application window
"""
import sys
from typing import NoReturn, Optional

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import (QApplication, QMainWindow, QShortcut, QDialog,
                             QFileDialog, QListWidgetItem)
from PyQt5.QtGui import QDesktopServices, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QUrl

from rabbitmark.definitions import MYVERSION, NOTAGS, SearchMode
from rabbitmark.librm import bookmark
from rabbitmark.librm import config
from rabbitmark.librm import database
from rabbitmark.librm import interchange
from rabbitmark.librm import readwise
from rabbitmark.librm import tag as tag_ops
from rabbitmark.librm.wayback_snapshot import request_snapshot

from .bookmark_table import BookmarkTableModel
from .forms.main import Ui_MainWindow
from .forms.about import Ui_Dialog as AboutForm
from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from . import import_dialog
from . import link_check_dialog
from . import wayback_search_dialog
from . import utils


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class MainWindow(QMainWindow):
    "RabbitMark application window."
    # pylint: disable=too-many-statements
    def __init__(self, sessionmaker) -> None:
        QMainWindow.__init__(self)
        self.form = Ui_MainWindow()
        self.form.setupUi(self)
        self.Session = sessionmaker
        self.session = self.Session()

        sf = self.form
        # File menu
        sf.actionShowPrivate.triggered.connect(self.onTogglePrivate)
        self.showPrivates = False
        sf.actionExport_CSV.triggered.connect(self.onExportCsv)
        sf.actionImport_CSV.triggered.connect(self.onImportCsv)
        sf.action_Quit.triggered.connect(self.quit)

        # Bookmark menu
        sf.actionNew.triggered.connect(self.onAddBookmark)
        sf.actionNew_from_clipboard.triggered.connect(
            self.onAddBookmarkFromClipboard)
        sf.actionWayBack.triggered.connect(self.onWayBackMachine)
        sf.actionDelete.triggered.connect(self.onDeleteBookmark)
        sf.actionCopyUrl.triggered.connect(self.onCopyUrl)
        sf.actionBrowseToUrl.triggered.connect(self.onBrowseForUrl)
        sf.actionSnapshotSite.triggered.connect(self.onSnapshotSite)
        sf.actionSendToReadwise.triggered.connect(self.onSendToReadwise)

        # Tag menu
        sf.actionRenameTag.triggered.connect(self.onRenameTag)
        sf.actionDeleteTag.triggered.connect(self.onDeleteTag)
        sf.actionMergeTag.triggered.connect(self.onMergeTag)

        # Tools menu
        sf.actionBrokenLinks.triggered.connect(self.onCheckBrokenLinks)
        sf.actionChangeReadwiseToken.triggered.connect(self.onChangeReadwiseToken)
        sf.actionChangeReadwiseToken.setVisible(
            config.exists(self.session, "readwise_api_token")
        )

        # Help menu
        sf.actionContents.triggered.connect(self.onHelpContents)
        sf.actionReportBug.triggered.connect(self.onReportBug)
        sf.actionAbout.triggered.connect(self.onAbout)

        # Not found on menus
        sf.tagsAllButton.clicked.connect(lambda: self.tagsSelect('all'))
        sf.tagsNoneButton.clicked.connect(lambda: self.tagsSelect('none'))
        sf.tagsInvertButton.clicked.connect(lambda: self.tagsSelect('invert'))

        findShortcut = QShortcut(QKeySequence("Ctrl+F"), sf.searchBox)
        findShortcut.activated.connect(self.onFocusFind)

        # Set up tag mode dropdown.
        # Indexes of these options should match with SearchMode.
        sf.tagsModeDropdown.addItem("Require at least one selected tag (OR)")
        sf.tagsModeDropdown.addItem("Require all selected tags (AND)")
        sf.tagsModeDropdown.activated.connect(self._updateForSearch)

        # set up data table
        self.tableView = self.form.bookmarkTable
        self.tableModel = BookmarkTableModel(self)
        self.tableView.setModel(self.tableModel)
        self.sm = self.tableView.selectionModel()
        self.sm.selectionChanged.connect(self.fillEditPane)
        self.tableView.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.tableView.setColumnWidth(0, 500)

        # set up tag list
        tag_counts = tag_ops.scan_tags_with_counts(self.session, self.showPrivates)
        self._fillTagList(tag_counts)
        self.form.tagList.itemSelectionChanged.connect(self.onCheckOptionAvailability)

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
    def _currentSearchMode(self) -> SearchMode:
        return SearchMode(self.form.tagsModeDropdown.currentIndex())

    @staticmethod
    def _makeTagItem(tag_name: str, count: int) -> QListWidgetItem:
        """Create a QListWidgetItem with display text
        'name (count)' and raw name in UserRole."""
        item = QListWidgetItem(f"{tag_name} ({count})")
        item.setData(Qt.UserRole, tag_name)
        return item

    @staticmethod
    def _tagName(item: QListWidgetItem) -> str:
        "Return the raw tag name stored in a tag list item."
        return item.data(Qt.UserRole)

    def _fillTagList(self, tag_counts: dict,
                     selected_names: Optional[set] = None) -> None:
        """Populate the tag list widget from tag_counts, ensuring NOTAGS
        is always the first item regardless of sort order."""
        self.form.tagList.clear()
        notags_count = tag_counts.get(NOTAGS)
        for tag_name, count in tag_counts.items():
            if tag_name == NOTAGS:
                continue
            item = self._makeTagItem(tag_name, count)
            self.form.tagList.addItem(item)
            if selected_names and tag_name in selected_names:
                item.setSelected(True)
        self.form.tagList.sortItems()
        if notags_count is not None:
            item = self._makeTagItem(NOTAGS, notags_count)
            self.form.tagList.insertItem(0, item)
            if selected_names and NOTAGS in selected_names:
                item.setSelected(True)

    def _findTagItem(self, tag_name: str) -> Optional[QListWidgetItem]:
        "Find a tag list item by its raw tag name (UserRole data)."
        for i in range(self.form.tagList.count()):
            item = self.form.tagList.item(i)
            if item.data(Qt.UserRole) == tag_name:
                return item
        return None

    def _getSingleTagName(self) -> Optional[str]:
        """
        Return the name of the single tag currently selected, or display an error
        message and return None if there is not exactly one tag selected.
        """
        tags = [self._tagName(i)
                for i in self.form.tagList.selectedItems()]

        if len(tags) < 1:
            utils.errorBox("Please select a tag.", "No tag selected")
            return None
        elif len(tags) > 1:
            utils.errorBox(
                "Tags cannot be edited in bulk. Please select exactly one tag.",
                "Cannot rename multiple tags")
            return None
        elif tags[0] == NOTAGS:
            utils.errorBox(
                f"You cannot edit '{NOTAGS}'. It is not a tag; rather, "
                f"it indicates that you would like to search for items that do not "
                f"have any tags.",
                "Item not editable")
            return None

        return tags[0]

    def _newBookmark(self, url) -> None:
        "Common portion of creating a new bookmark."
        # Create the new item with any tags that are selected.
        tags = [self._tagName(i)
                for i in self.form.tagList.selectedItems()
                if self._tagName(i) != NOTAGS]

        # Full-text filter is automatically cleared on add -- otherwise, the new
        # item won't be visible!
        self.form.searchBox.setText("")
        self._updateForSearch()
        # If in AND mode, turn off "no tags" mode, or it similarly won't be visible.
        if self._currentSearchMode() == SearchMode.And:
            self.form.tagList.item(0).setSelected(False)

        newBookmark = bookmark.add_bookmark(self.session, url, tags)
        self.session.commit()  # pylint: disable=no-member

        self._resetTagList()
        self._updateForSearch()
        index = self.tableModel.indexFromPk(newBookmark.id)
        if index is not None:
            self.tableView.setCurrentIndex(index)
            self.detailsForm.nameBox.selectAll()
            self.detailsForm.nameBox.setFocus()

    def _reselectItem(self, item=None, fill_edit_pane=True) -> None:
        """
        Select the given /item/ if it still exists in the view, or the first
        item in the view if it doesn't or /item/ is None.

        This method should be called after updating the table view using a
        resetModel() command, as that causes the loss of the current selection.

        Arguments:
            item (default None) - if not None, attempt to select the item by
                this primary key.
            fill_edit_pane - if True, repopulate the edit pane from the
                database. Set to False when the edit pane already has the
                correct content (e.g., after an auto-save).
        """
        if item is None:
            idx = self.tableModel.index(0, 0)
        else:
            idx = self.tableModel.indexFromPk(item)
            if idx is None: # provided item isn't in this view
                idx = self.tableModel.index(0, 0)

        if not fill_edit_pane:
            with utils.signalsBlocked(self.sm):
                self.tableView.setCurrentIndex(idx)
        else:
            self.tableView.setCurrentIndex(idx)
            self.fillEditPane()
        self.onCheckOptionAvailability()  # after resetting the edit pane

    def _resetTagList(self) -> None:
        """
        Rebuild the tag list widget from the database.
        Signals are blocked during rebuild; callers must handle _updateForSearch
        explicitly if needed.
        """
        # Save selected tag names.
        selectedNames = {self._tagName(i)
                         for i in self.form.tagList.selectedItems()}

        tag_counts = tag_ops.scan_tags_with_counts(self.session, self.showPrivates)

        # Rebuild list with signals blocked to avoid spurious updates.
        with utils.signalsBlocked(self.form.tagList):
            self._fillTagList(tag_counts, selectedNames)

    def _updateTitleCount(self, count) -> None:
        """
        Change the count of matching items that appears in the title bar to
        /count/.
        """
        self.setWindowTitle(f"RabbitMark - {count} match{'' if count == 1 else 'es'}")

    def _updateForSearch(self, *_args, fill_edit_pane=True) -> None:
        """
        Update the bookmarks table to match the filter and tag selection.

        We determine and pass the text in the filter box and a list of the tags
        selected, and we restore the selection to the currently selected
        bookmark after the view is refreshed if that bookmark is still in the
        new view.
        """
        selectedTags = [self._tagName(i)
                        for i in self.form.tagList.selectedItems()]
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        oldId = None if mark is None else mark.id
        searchMode = self._currentSearchMode()

        nameText = "%" + self.form.searchBox.text() + "%"
        marks = bookmark.find_bookmarks(self.session, nameText, selectedTags,
                                        self.showPrivates, searchMode)

        header = self.tableView.horizontalHeader()
        saved_col = header.sortIndicatorSection()
        saved_order = header.sortIndicatorOrder()

        self.tableModel.updateContents(marks)
        self.tableModel.sort(saved_col, saved_order)
        header.setSortIndicator(saved_col, saved_order)

        self._reselectItem(oldId, fill_edit_pane=fill_edit_pane)
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
        sfdw = self.detailsForm
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
                self._updateForSearch(fill_edit_pane=False)

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
    # File
    def onExportCsv(self) -> None:
        "Export bookmarks to CSV."
        fname = QFileDialog.getSaveFileName(
            caption="Export Bookmarks to CSV",
            filter="CSV files (*.csv);;All files (*)"
        )[0]
        if not fname:
            return
        fname = utils.forceExtension(fname, "csv")
        num = interchange.export_bookmarks_to_csv(self.session, fname)
        utils.informationBox(f"Successfully exported {num} bookmarks.",
                             "Export Bookmarks to CSV")

    def onImportCsv(self) -> None:
        "Import bookmarks from CSV."
        fname = QFileDialog.getOpenFileName(
            caption="Import Bookmarks from CSV",
            filter="CSV files (*.csv);;All files (*)"
        )[0]
        if not fname:
            return
        dlg = import_dialog.ImportDialog(self, self.session, fname)
        dlg.exec_()

        # Since we could have edited things within the dialog, we need to resync.
        self._updateForSearch()
        self._resetTagList()

    # Bookmarks
    def onAddBookmark(self) -> None:
        "Create a new bookmark without a given URL."
        self._newBookmark("http://")

    def onAddBookmarkFromClipboard(self) -> None:
        "Create a new bookmark from the URL on the clipboard."
        clipboard = QApplication.clipboard()
        pastedUrl = str(clipboard.text()).strip()  # type: ignore[union-attr]
        if '://' not in pastedUrl:
            utils.warningBox("No protocol (e.g., http://) in URL. Adding "
                             "http:// to beginning. You may wish to check "
                             "the URL.", "URL possibly invalid")
            pastedUrl = 'http://' + pastedUrl
        self._newBookmark(pastedUrl)

    def onBrowseForUrl(self) -> None:
        QDesktopServices.openUrl(QUrl(self.detailsForm.urlBox.text()))

    def onCopyUrl(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.detailsForm.urlBox.text())  # type: ignore[union-attr]

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
        if nextRow is not None:
            self.tableView.setCurrentIndex(nextRow)
        self.fillEditPane()

    def onWayBackMachine(self) -> None:
        "Find a snapshot of the item's URL in the WayBackMachine."
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        archiveUrl = wayback_search_dialog.init_wayback_search(self, mark.url)
        if archiveUrl is not None:
            self.detailsForm.urlBox.setText(archiveUrl)
            self.maybeSaveBookmark(self.detailsForm.urlBox, None)

    def onSnapshotSite(self) -> None:
        "Ask the WayBackMachine to take a snapshot of the selected site now."
        mark = self.tableModel.getObj(self.tableView.currentIndex())
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            request_snapshot(mark.url)
        except Exception as e:
            utils.errorBox(f"Sorry, your request did not complete successfully. "
                           f"That's about all we can know, but here's a little more:\n"
                           f"{str(e)}")
            return
        finally:
            QApplication.restoreOverrideCursor()
        utils.informationBox(
            "The WayBackMachine reports that it has archived this site. "
            "You can now search for the snapshot.")


    # Readwise Reader
    def _ensureReadwiseToken(self) -> Optional[str]:
        """
        Return the Readwise Reader API token, prompting the user to enter one
        if it hasn't been configured yet. Returns None if the user cancels.
        """
        token = config.get(self.session, "readwise_api_token")
        if token:
            return token

        utils.informationBox(
            "You haven't yet entered a Readwise access token. You can obtain one "
            'at <a href="https://readwise.io/access_token">https://readwise.io/access_token</a>. '
            "After clicking OK, you'll be prompted to paste the access token.",
            "Access Token"
        )

        token, accepted = utils.inputBox(
            "Readwise Reader access token:",
            "Enter Access Token"
        )
        if not accepted or not token.strip():
            return None
        else:
            utils.informationBox(
                "Saved access token. You can change the access token at any time "
                "from Tools > Change Readwise Reader Access Token.",
                "Token Saved"
            )

        token = token.strip()
        config.put(self.session, "readwise_api_token", token)
        self.session.commit()
        self.form.actionChangeReadwiseToken.setVisible(True)
        return token

    def onSendToReadwise(self) -> None:
        "Send the selected bookmark to Readwise Reader."
        token = self._ensureReadwiseToken()
        if token is None:
            return

        last_tags = config.get(self.session, "readwise_last_tags") or ""
        reader_tags, accepted = utils.inputBox(
            "Tags (comma-separated):",
            "Send to Readwise Reader",
            last_tags
        )
        if not accepted:
            return

        mark = self.tableModel.getObj(self.tableView.currentIndex())
        tags = [t.strip() for t in reader_tags.split(",") if t.strip()]

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            readwise.save_to_reader(
                api_token=token,
                url=mark.url,
                title=mark.name,
                summary=mark.description,
                tags=tags,
            )
        except Exception as e:
            utils.errorBox(
                f"Failed to send to Readwise Reader:\n{e}",
                "Send to Readwise Reader")
            return
        finally:
            QApplication.restoreOverrideCursor()

        config.put(self.session, "readwise_last_tags", reader_tags)
        self.session.commit()

    def onChangeReadwiseToken(self) -> None:
        "Change the stored Readwise Reader API token."
        current = config.get(self.session, "readwise_api_token") or ""
        new_token, accepted = utils.inputBox(
            "Readwise Reader access token:",
            "Change Readwise Reader Access Token",
            current
        )
        if accepted:
            config.put(self.session, "readwise_api_token", new_token.strip())
            self.session.commit()

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
            self.session.commit()
            self._resetTagList()
            self._updateForSearch()
            self.fillEditPane()

    def onMergeTag(self) -> None:
        "Merge the selected tag into another."
        tag = self._getSingleTagName()
        if tag is None:
            return

        new, doContinue = utils.inputBox(f"Merge tag '{tag}' into:", "Merge tag")
        if doContinue:
            if tag_ops.merge_tags(self.session, tag, new):
                self.session.commit()
                self._resetTagList()
                self._updateForSearch()
                self.fillEditPane()
            # select the tag we merged into
            merged_item = self._findTagItem(new)
            if merged_item:
                merged_item.setSelected(True)

    def onRenameTag(self) -> None:
        "Rename the selected tag."
        tag = self._getSingleTagName()
        if tag is None:
            return

        new, doContinue = utils.inputBox("New name for tag:", "Rename tag", tag)
        if doContinue:
            if tag_ops.rename_tag(self.session, tag, new):
                self.session.commit()
                self._resetTagList()
                self._updateForSearch()
                self.fillEditPane()
            else:
                utils.errorBox("A tag by that name already exists.",
                               "Cannot rename tag")

            # select the newly renamed tag
            renamed_item = self._findTagItem(new)
            if renamed_item:
                renamed_item.setSelected(True)

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

    @staticmethod
    def onHelpContents() -> None:
        "Display the manual."
        # TODO: Update with real URL
        QDesktopServices.openUrl(QUrl("https://github.com/sobjornstad/rabbitmark#readme"))

    @staticmethod
    def onReportBug() -> None:
        "Open the GitHub issues page."
        # TODO: Update with real URL
        QDesktopServices.openUrl(QUrl("https://github.com/sobjornstad/rabbitmark/issues/new"))

    def onAbout(self) -> None:
        "Load the About screen to display metadata on and an description of RabbitMark."
        class AboutWindow(QDialog):
            "Simple window to show the about form, with the current app version."
            def __init__(self):
                super().__init__()
                self.form = AboutForm()
                self.form.setupUi(self)
                self.form.versionLabel.setText(
                    f'<span style="font-size: 12pt;">Version {MYVERSION}</span>')
                self.form.okButton.clicked.connect(self.accept)
        dlg = AboutWindow()
        dlg.exec_()

    def onCheckOptionAvailability(self) -> None:
        "Update the enabled/disabled state of menus based on the current selection."
        sf = self.form

        bookmarkActions = (
            sf.actionWayBack,
            sf.actionDelete,
            sf.actionCopyUrl,
            sf.actionBrowseToUrl,
            sf.actionSnapshotSite,
            sf.actionSendToReadwise,
        )
        tagActions = (
            sf.actionRenameTag,
            sf.actionDeleteTag,
            sf.actionMergeTag,
        )

        bookmarkSelected = bool(self.tableModel.getObj(self.tableView.currentIndex()))
        tagSelList = self.form.tagList.selectedItems()
        tagSelected = bool(tagSelList) and not self._tagName(tagSelList[0]) == NOTAGS
        multipleTagsSelected = len(tagSelList) > 1

        for action in bookmarkActions:
            action.setEnabled(bookmarkSelected)
        for action in tagActions:
            action.setEnabled(tagSelected and not multipleTagsSelected)


    def closeEvent(self, _evt) -> NoReturn:
        "Catch click of the X button, etc., and properly quit."
        self.quit()

    def quit(self) -> NoReturn:
        "Clean up and quit RabbitMark."
        # fake changing focus: the widget name for new is arbitrary,
        # one of the editable boxes is required for old
        self.maybeSaveBookmark(old=self.detailsForm.nameBox,
                               new=self.detailsForm.nameBox)
        # Double-check we don't have any uncommitted changes.
        self.session.commit()
        self.session.close()
        sys.exit(0)


def start() -> None:
    "Application entry point."
    sessionmaker = database.make_Session()
    app = QApplication(sys.argv)
    mw = MainWindow(sessionmaker)
    app.focusChanged.connect(mw.maybeSaveBookmark)
    mw.show()
    app.exec_()
