"""
wayback_search_dialog.py -- interface for searching the WayBackMachine
"""

from typing import Optional, List

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSignal, QThread, QUrl

from rabbitmark.librm import bookmark
from rabbitmark.librm import broken_links
from rabbitmark.librm.broken_links import LinkCheck

from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from .forms.linkcheck import Ui_Dialog as Ui_LinkCheckDialog
from .forms.linkcheck_progress import Ui_Dialog as Ui_LinkCheckProgressDialog
from . import wayback_search_dialog
from . import utils


class LinkCheckDialog(QDialog):
    """
    Do stuff
    """
    def __init__(self, parent, blinks, session) -> None:
        "Set up the dialog."
        QDialog.__init__(self)
        self.form = Ui_LinkCheckDialog()
        self.form.setupUi(self)
        self.parent = parent
        self.blinks = {i.name: i for i in blinks}
        self.session = session

        # set up details widget
        self.detailsForm = BookmarkDetailsWidget()
        self.detailsForm.setupUi(self.form.detailsWidget)
        self.detailsForm.browseUrlButton.clicked.connect(self.onBrowseUrl)
        self.detailsForm.copyUrlButton.clicked.connect(self.onCopyUrl)

        self.form.pageList.addItems(sorted(self.blinks.keys()))
        self.form.pageList.item(0).setSelected(True)
        self.form.pageList.currentItemChanged.connect(self.updateDetailsPane)

        # link up buttons
        self.form.closeButton.clicked.connect(self.accept)
        self.form.deleteButton.clicked.connect(self.onDeleteBookmark)
        self.form.wayBackMachineButton.clicked.connect(self.onWaybackBookmark)
        self.form.dismissButton.clicked.connect(self.onDismissBookmark)

        # Start cursor in page list. In order to get the tab order to work with the
        # additional widget (which Designer doesn't let us set the tab order of
        # within the main form), the last position in the main form's tab order
        # must be the item immediately before where the widget should be positioned
        # in the order. This works great, but means that without an explicit set
        # focus, the cursor starts with the item just after the widget selected,
        # which is a random action button.
        self.form.pageList.setFocus()

    def accept(self):
        "Save any bookmark we were still editing and close the dialog."
        try:
            self.saveBookmark()
        except KeyError:
            # last item was just removed
            pass
        super().accept()

    def reject(self):
        "Redirect to standard accept() if Esc pressed or X button clicked."
        return self.accept()

    def _blinkAndMark(self, widgetItem=None):
        """
        Return the link and bookmark objects for the specified list widget
        item, or the currently selected one if not specified.
        """
        if widgetItem is None:
            widgetItem = self.form.pageList.selectedItems()[0]

        blink_obj = self.blinks[widgetItem.text()]
        mark = bookmark.get_bookmark_by_id(self.session, blink_obj.pk)
        return blink_obj, mark

    def updateDetailsPane(self, new, previous):
        """
        Fill the editor/details pane with data from the currently selected bookmark.

        If /initial/, this is our first selection and we should thus skip saving
        before updating (otherwise we'd just blank out the first item in the list).
        """
        sfdw = self.detailsForm
        if previous is not None:
            try:
                _, prevMark = self._blinkAndMark(previous)
            except KeyError:
                # item was just deleted
                pass
            else:
                self.saveBookmark(prevMark)

        if new is not None:
            blink_obj, mark = self._blinkAndMark(new)
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

            err_des = blink_obj.error_description
            err_code = blink_obj.status_code
            self.form.detailsBox.setText(err_des if err_des is not None else "")
            self.form.statusCodeBox.setText(str(err_code)
                                            if err_code is not None else "")
        else:
            # We've handled all the items. Close the dialog.
            self.accept()

    def onBrowseUrl(self) -> None:
        QDesktopServices.openUrl(QUrl(self.detailsForm.urlBox.text()))

    def onCopyUrl(self) -> None:
        QApplication.clipboard().setText(self.detailsForm.urlBox.text())

    def onDeleteBookmark(self):
        "Delete a broken link from the database."
        _, mark = self._blinkAndMark()
        del self.blinks[mark.name]
        self.form.pageList.takeItem(self.form.pageList.currentRow())
        bookmark.delete_bookmark(self.session, mark)
        self.session.commit()

    def onWaybackBookmark(self):
        "Replace the bookmark's URL with a WayBackMachine version."
        _, mark = self._blinkAndMark()
        new_url = wayback_search_dialog.init_wayback_search(self, mark.url)
        if new_url is not None:
            self.detailsForm.urlBox.setText(new_url)
            self.detailsForm.urlBox.setFocus()

    def onDismissBookmark(self):
        "Remove a bookmark from the list (when we're done dealing with it)."
        self.saveBookmark()
        _, mark = self._blinkAndMark()
        del self.blinks[mark.name]
        self.form.pageList.takeItem(self.form.pageList.currentRow())

    def saveBookmark(self, mark=None):
        "Save the specified bookmark, or the currently selected one if not specified."
        if mark is None:
            _, mark = self._blinkAndMark()
        if bookmark.save_if_edited(self.session, mark,
                                   utils.mark_dictionary(self.detailsForm)):
            self.session.commit()  # pylint: disable=no-member


class LinkCheckThread(QThread):
    """
    Worker thread to scan for broken links.
    """
    progress_update = pyqtSignal(int, int, int, str)

    def __init__(self, sessionmaker) -> None:
        super().__init__()
        self.blinks: List[LinkCheck] = []
        self.link_success_count = 0
        self.link_fail_count = 0
        self.exception: Optional[Exception] = None
        self.sessionmaker = sessionmaker

    def run(self) -> None:
        """
        Create database session for this thread, then call into
        broken_links.scan() using it. The callback for scan tracks progress
        and reports it to the calling dialog and saves off any failures as
        they occur where they can be collected at the end of the check.
        """
        def callback(at: int, tot: int, obj: LinkCheck) -> None:
            if obj.successful:
                self.link_success_count += 1
            else:
                self.blinks.append(obj)
                self.link_fail_count += 1
            assert at == self.link_fail_count + self.link_success_count

            log_str = f"{at:03d}/{tot:03d} {obj}"
            self.progress_update.emit(self.link_success_count,
                                      self.link_fail_count, tot, log_str)

        try:
            session = self.sessionmaker()
            broken_links.scan(session, callback, only_failures=False)
            session.close()
        except Exception as e:  # pylint: disable=broad-except
            self.exception = e


class LinkCheckProgressDialog(QDialog):
    """
    Prior to showing the LinkCheckDialog, we need to actually check the links
    and compile a list of links that aren't working. This dialog shows progress
    while performing those steps.
    """
    def __init__(self, parent, sessionmaker) -> None:
        QDialog.__init__(self)
        self.form = Ui_LinkCheckProgressDialog()
        self.form.setupUi(self)
        self.parent = parent
        self.sessionmaker = sessionmaker

        self.lct: Optional[LinkCheckThread] = None
        self.blinks: List[LinkCheck] = []

        self.form.cancelButton.clicked.connect(self.reject)

    def start(self) -> None:
        "Start a worker thread which coordinates scanning of the links."
        self.lct = LinkCheckThread(self.sessionmaker)
        self.lct.finished.connect(self.join_thread)
        self.lct.progress_update.connect(self.update_progress)
        self.lct.start()

    def update_progress(self, success: int, fail: int, tot: int, log: str) -> None:
        "Update the progress data. Called after every scan is completed."
        self.form.okLabel.setText(f"OK: {success}")
        self.form.failedLabel.setText(f"Failed: {fail}")
        self.form.totalLabel.setText(f"Total: {tot}")
        self.form.progressBar.setValue(int((success + fail) * 100 / tot))
        self.form.progressLog.appendPlainText(log)

    def join_thread(self) -> None:
        """
        Clean up when the worker thread terminates. Gather up the results,
        raise any exceptions that might have occurred in the thread (none are
        *supposed* to happen, but better to find out about them if they do!),
        and transfer the list of failed links to the 'blinks' property where
        the user of this dialog can grab them. Then accept the dialog.
        """
        assert self.lct is not None, "Tried to join a not-started thread!"
        if self.lct.exception:
            self.reject()
            raise self.lct.exception

        self.blinks = self.lct.blinks
        self.accept()
