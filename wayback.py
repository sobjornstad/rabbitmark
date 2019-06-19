"""
wayback.py -- class for searching the WayBackMachine
"""

import datetime
import requests

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from forms.archivesearch import Ui_Dialog as Ui_ArchiveDialog
import utils


class WayBackDialog(QDialog):
    """
    Allow the user to search through the snapshots provided by the
    WayBackMachine using a binary search algorithm.

    To set up the dialog, snapshotData must be provided to the constructor;
    snapshot data consists of a list of tuples containing a formatted timestamp
    (in whatever format the user should see it), a raw timestamp (format
    '%Y%m%d%H%M%S'), and the full URL to that snapshot on the web.

    When the user has made a selection, exec_() will return an index value into
    the snapshotData list corresponding to the snapshot the user selected, or
    -1 if the user cancelled the dialog.
    """

    state_label_template = "You are at snapshot %i, bisecting %i to %i (%i " \
                           "total snapshots).\nHow do you want to proceed?"
    snapshot_label_template = "The following snapshot is from %s:"

    def __init__(self, parent, snapshotData):
        """
        Set up the dialog as usual.

        Arguments:
            parent - parent widget, as normal
            snapshotData - see the class docstring.
        """
        QDialog.__init__(self)
        self.form = Ui_ArchiveDialog()
        self.form.setupUi(self)
        self.parent = parent

        self.form.useRadio.setChecked(True)
        self.form.okButton.clicked.connect(self.onContinue)
        self.form.copyButton.clicked.connect(self.onCopy)
        self.form.browseButton.clicked.connect(self.onBrowseTo)

        self.sd = snapshotData # list of snapshots
        self.lower = None      # lowest possible target snapshot index
        self.upper = None      # highest possible target snapshot index
        self.curnt = None      # current snapshot index
        self.stack = []        # history of past values of 3 variables above
        self.proceed('start')

    def reject(self):
        """
        0 is a possible return value on accept, meaning to use the first
        snapshot in the list, so we have to redefine reject()'s traditional
        return value of 0 as -1.
        """
        QDialog.done(self, -1)

    def onCopy(self):
        "Copy URL to clipboard -- same as in MainWindow."
        QApplication.clipboard().setText(self.form.urlBox.text())

    def onBrowseTo(self):
        "Browse to shown URL -- same as in MainWindow."
        QDesktopServices.openUrl(QUrl(self.form.urlBox.text()))

    def proceed(self, action):
        """
        Move a step forward in our binary search algorithm.

        The single argument /action/ is one of the following strings:
            'start'   - initialize the algorithm, starting at latest snapshot
            'later'   - say that the target snapshot is more recent than
                        current
            'earlier' - say that the target snapshot is older than current
            'backup'  - pop control vars off the stack and go back one step in
                        the search algorithm
        Other values will raise an AssertionError.

        This method assumes that the action requested is valid with the current
        values of the control variables; the interface is responsible for
        making sure the user cannot select an invalid action. At the end of
        proceed() we call self.checkAllowableActions(), which is responsible
        for disabling options that could result in this method receiving an
        invalid action.
        """

        # Save current search parameters to a stack for later undo before
        # beginning an action that changes them.
        if action in ('earlier', 'later'):
            self.stack.append((self.lower, self.upper, self.curnt))

        # Process the provided action.
        if action == 'start':
            self.lower = 0
            self.upper = len(self.sd) - 1
            self.curnt = self.upper
        elif action == 'later':
            self.lower = self.curnt + 1
            increaseBy = (self.upper - self.curnt + 1) // 2
            self.curnt = self.curnt + increaseBy
        elif action == 'earlier':
            self.upper = self.curnt - 1
            decreaseBy = (self.curnt - self.lower + 1) // 2
            self.curnt = self.curnt - decreaseBy
        elif action == 'backup':
            self.lower, self.upper, self.curnt = self.stack.pop()
        else:
            assert False, "Invalid action!"
        self.checkAllowableActions()
        self.updateDialogText()

    def updateDialogText(self):
        """
        Update the dialog box to show the user appropriate details about the
        state of the search.

        This method should be called after proceed() is done.
        """
        tstamp, _, url = self.sd[self.curnt]
        self.form.urlBox.setText(url)
        self.form.urlBox.setCursorPosition(0)

        # note: display converted to 1-based indexing for user-friendliness
        if len(self.sd) > 1 and self.curnt+1 == 1:
            state = "This is the oldest of %i snapshots.\n" \
                    "What do you want to do?" % len(self.sd)
        elif len(self.sd) > 1 and self.curnt+1 == len(self.sd):
            state = "This is the most recent of %i snapshots.\n" \
                    "What do you want to do?" % len(self.sd)
        elif len(self.sd) == 1:
            state = "This is the only available snapshot.\n" \
                    "What do you want to do?"
        else:
            state = self.state_label_template % (
                self.curnt+1, self.lower+1, self.upper+1, len(self.sd))
        self.form.stateLabel.setText(state)
        self.form.snapshotLabel.setText(self.snapshot_label_template % tstamp)

    def checkAllowableActions(self):
        """
        Determine which search actions make sense to allow with the current
        state of the search (for instance, it doesn't make sense to try a newer
        snapshot when the current snapshot is equal to the upper bound), and
        disable those that don't. Additionally, reselect the "use" option.

        This method should be called after proceed() is done.
        """
        sf = self.form
        sf.newerRadio.setEnabled(self.upper > self.curnt)
        sf.olderRadio.setEnabled(self.lower < self.curnt)
        sf.backupRadio.setEnabled(len(self.stack) > 0)
        sf.useRadio.setChecked(True)

    def onContinue(self):
        """
        Runs when "OK" is clicked. If "use" or "cancel" is selected, the dialog
        is accepted or rejected as appropriate; if another option is selected,
        proceed() is called to move another step into the search algorithm.
        """
        if self.form.useRadio.isChecked():
            self.done(self.curnt)
        elif self.form.newerRadio.isChecked():
            self.proceed('later')
        elif self.form.olderRadio.isChecked():
            self.proceed('earlier')
        elif self.form.backupRadio.isChecked():
            self.proceed('backup')
        elif self.form.cancelRadio.isChecked():
            self.reject()
        else:
            assert False, "No radio button selected! This should be " \
                          "impossible."


def way_back_from_url(parent, original_url: str):
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

    requestUrl = "http://web.archive.org/cdx/search/cdx?url=%s&output=json"
    result = requests.get(requestUrl % original_url)
    try:
        # If no results, .json() may raise ValueError or just return None.
        snapshots = result.json()
        if not snapshots:
            raise ValueError
    except ValueError:
        QApplication.restoreOverrideCursor()
        utils.informationBox("Sorry, the WayBackMachine does not have "
                             "this page archived.", "Page not found")
        return

    archived = []
    for i in snapshots[1:]: # first row is headers
        timestamp, pagePath = i[1], i[2]
        formattedTimestamp = datetime.datetime.strptime(
            timestamp, '%Y%m%d%H%M%S').strftime(utils.DATE_FORMAT)
        archivedUrl = "http://web.archive.org/web/%s/%s" % (
            timestamp, pagePath)
        archived.append((formattedTimestamp, timestamp, archivedUrl))

    QApplication.restoreOverrideCursor()
    dlg = WayBackDialog(parent, archived)
    snapshotIndex = dlg.exec_()

    if snapshotIndex == -1:
        return None
    else:
        return archived[snapshotIndex][2]
