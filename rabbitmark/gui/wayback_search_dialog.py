"""
wayback_search_dialog.py -- interface for searching the WayBackMachine
"""

import re
from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices, QCursor
from PyQt5.QtCore import QUrl, Qt

from rabbitmark.definitions import DATE_FORMAT
from rabbitmark.librm import binary_search
from rabbitmark.librm import wayback_snapshot

from .forms.archivesearch import Ui_Dialog as Ui_ArchiveDialog
from . import utils


class WayBackDialog(QDialog):
    """
    Allow the user to search through the snapshots provided by the
    WayBackMachine using a binary search algorithm.

    To set up the dialog, a sequence of WaybackSnapshots must be provided to
    the constructor; these can be obtained by a call to
    wayback_snapshot.get_snapshots().

    When the user has made a selection, exec_() will return an index value into
    the snapshotData list corresponding to the snapshot the user selected, or
    -1 if the user cancelled the dialog.
    """
    state_label_template = (
        "You are at snapshot %i, bisecting %i to %i (%i total snapshots).\n"
        "%s\n"
        "How do you want to proceed?")
    snapshot_label_template = "The following snapshot is from %s.%s"

    def __init__(self, parent, snapshots) -> None:
        """
        Set up the dialog as usual.

        Arguments:
            parent - parent widget, as normal
            snapshots - see the class docstring.
        """
        QDialog.__init__(self)
        self.form = Ui_ArchiveDialog()
        self.form.setupUi(self)
        self.parent = parent

        self.form.useRadio.setChecked(True)
        self.form.okButton.clicked.connect(self.onContinue)
        self.form.copyButton.clicked.connect(self.onCopy)
        self.form.browseButton.clicked.connect(self.onBrowseTo)

        self.sd = snapshots
        self.bs = binary_search.BisectionState(num_items=len(self.sd),
                                               start_at_end=True)

        self._checkAllowableActions()
        self._updateDialogText()

    def reject(self) -> None:
        """
        0 is a possible return value on accept, meaning to use the first
        snapshot in the list, so we have to redefine reject()'s traditional
        return value of 0 as -1.
        """
        QDialog.done(self, -1)

    def _checkAllowableActions(self) -> None:
        """
        Determine which search actions make sense to allow with the current
        state of the search and disable those that don't.
        Additionally, reselect the "use" option.
        """
        sf = self.form
        sf.newerRadio.setEnabled(self.bs.can_go_after)
        sf.olderRadio.setEnabled(self.bs.can_go_before)
        sf.backupRadio.setEnabled(self.bs.can_backtrack)
        sf.useRadio.setChecked(True)

    def _updateDialogText(self) -> None:
        """
        Update the dialog box to show the user appropriate details about the
        state of the search.

        This method should be called after proceed() is done.
        """
        current_item = self.sd[self.bs.index]
        snapshot_time = current_item.formatted_timestamp(DATE_FORMAT)
        if re.match("[-45]", current_item.response):
            if current_item.response == "-":
                err = "Unspecified error"
            else:
                err = f"Error {current_item.response}"
            snapshot_response_code = (
                f"\n** {err} at crawl time. "
                f"This snapshot probably will not work. **")
        else:
            snapshot_response_code = ""

        wut_do = "\nWhat do you want to do?"
        if self.bs.at_only:
            state = f"This is the only available snapshot.{wut_do}"
        elif self.bs.at_start:
            state = f"This is the oldest of {self.bs.num_items} snapshots.{wut_do}"
        elif self.bs.at_end:
            state = f"This is the most recent of {self.bs.num_items} snapshots.{wut_do}"
        else:
            # Convert display to one-based indexing for user-friendliness.
            state = self.state_label_template % (
                self.bs.index+1, self.bs.lower+1,
                self.bs.upper+1, self.bs.num_items,
                _stepsAfter(self.bs.remaining_steps))

        self.form.stateLabel.setText(state)
        self.form.snapshotLabel.setText(
            self.snapshot_label_template % (snapshot_time, snapshot_response_code))
        self.form.urlBox.setText(current_item.archived_url)
        self.form.urlBox.setCursorPosition(0)

    def onBrowseTo(self) -> None:
        "Browse to shown URL -- same as in MainWindow."
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def onCopy(self) -> None:
        "Copy URL to clipboard -- same as in MainWindow."
        QApplication.clipboard().setText(self.form.urlBox.text())

    def onContinue(self) -> None:
        """
        Runs when "OK" is clicked. If "use" or "cancel" is selected, the dialog
        is accepted or rejected as appropriate; if another option is selected,
        proceed() is called to move another step into the search algorithm.
        """
        if self.form.useRadio.isChecked():
            self.done(self.bs.index)
        elif self.form.newerRadio.isChecked():
            self.bs.mark_after()
        elif self.form.olderRadio.isChecked():
            self.bs.mark_before()
        elif self.form.backupRadio.isChecked():
            self.bs.backtrack()
        elif self.form.cancelRadio.isChecked():
            self.reject()
        else:
            assert False, "No radio button selected! This should be " \
                          "impossible."

        self._checkAllowableActions()
        self._updateDialogText()


def way_back_from_url(parent, original_url: str) -> Optional[str]:
    """
    Find a URL from the WayBackMachine that can replace the current URL
    (presumably if the formerly working URL has stopped working, or perhaps
    if we just want to make sure it will work in the future or save a
    particular version of the page).

    This method requests a list of snapshots from the CDX (more
    complicated) WayBackMachine API on archive.org, then creates a
    WayBackDialog to allow the user to find a snapshot that contains the
    content they were hoping for. Finally, it rewrites the value in the
    URLbox (which will result in it being saved when the focus changes,
    just as when the user edits it) to match the new snapshot.

    Returns None if the user canceled the process, or the new URL if one was
    selected.
    """
    snapshots = wayback_snapshot.get_snapshots(original_url)
    QApplication.restoreOverrideCursor()

    if not snapshots:
        utils.informationBox("Sorry, the WayBackMachine does not have "
                             "this page archived.", "Page not found")
        return None

    dlg = WayBackDialog(parent, snapshots)
    snapshotIndex = dlg.exec_()
    if snapshotIndex == -1:
        return None
    else:
        return snapshots[snapshotIndex].archived_url


def init_wayback_search(parent, url: str) -> Optional[str]:
    """
    Launch a WayBackMachine search dialog for /url/ with widget /parent/.
    If the URL is already of a WBM snapshot, warn the user and let them cancel.

    Return:
        - A URL if one should replace the existing URL.
        - None if the user canceled at any point in the process.
    """
    if re.match("https?://web.archive.org/", url):
        if utils.questionBox(
                "This bookmark appears to already be pointing at a snapshot in "
                "the WayBackMachine. Would you like to pick a new snapshot?",
                "Select new snapshot?"):
            new_url = re.sub("https?://web.archive.org/web/[0-9]+/(.*)", r"\1", url)
        else:
            return None
    else:
        new_url = url

    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    return way_back_from_url(parent, new_url)


def _stepsAfter(steps: int) -> str:
    "Get an appropriate string describing the number of steps left in a binary search."
    if steps == 0:
        return "This is the final step."
    elif steps == 1:
        return "1 step after this one."
    else:
        return f"≤{steps} steps after this one."
