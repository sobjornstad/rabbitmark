"""
wayback_search_dialog.py -- interface for searching the WayBackMachine
"""

from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from .librm import bookmark

from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from .forms.linkcheck import Ui_Dialog as Ui_LinkCheckDialog
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

        self.form.pageList.addItems(sorted(self.blinks.keys()))
        self.form.pageList.item(0).setSelected(True)
        self.form.pageList.itemSelectionChanged.connect(self.updateDetailsPane)
        self.updateDetailsPane()

        # link up buttons
        self.form.closeButton.clicked.connect(self.accept)
        self.form.deleteButton.clicked.connect(self.onDeleteBookmark)
        self.form.wayBackMachineButton.clicked.connect(self.onWaybackBookmark)

    def _selectedBlinkAndMark(self):
        "Return the link and bookmark objects for the selected item."
        blink_obj = self.blinks[self.form.pageList.selectedItems()[0].text()]
        mark = bookmark.get_bookmark_by_id(self.session, blink_obj.pk)
        return blink_obj, mark


    def updateDetailsPane(self):
        """
        Fill the editor/details pane with data from the currently selected bookmark.
        """
        sfdw = self.detailsForm
        blink_obj, mark = self._selectedBlinkAndMark()

        #TODO: Refactor so this isn't a copy of the one in main
        sfdw.nameBox.setText(mark.name)
        sfdw.urlBox.setText(mark.url)
        sfdw.descriptionBox.setPlainText(mark.description)
        sfdw.privateCheck.setChecked(mark.private)
        tags = ', '.join([i.text for i in mark.tags])
        sfdw.tagsBox.setText(tags)
        # If a name or URL is too long to fit in the box, this will make
        # the box show the beginning of it rather than the end.
        for i in (sfdw.nameBox, sfdw.urlBox, sfdw.tagsBox):
            i.setCursorPosition(0)

        err_des = blink_obj.error_description
        err_code = blink_obj.status_code
        self.form.detailsBox.setText(err_des if err_des is not None else "")
        self.form.statusCodeBox.setText(str(err_code) if err_code is not None else "")

    def onDeleteBookmark(self):
        "Delete a broken link from the database."
        blink_obj, mark = self._selectedBlinkAndMark()
        del self.blinks[mark.name]
        self.form.pageList.takeItem(self.form.pageList.currentRow())
        bookmark.delete_bookmark(self.session, mark)
        self.session.commit()

    def onWaybackBookmark(self):
        "Replace the bookmark's URL with a WayBackMachine version."
        blink_obj, mark = self._selectedBlinkAndMark()
        new_url = wayback_search_dialog.init_wayback_search(self, mark.url)
        if new_url is not None:
            # TODO: Need to set the actual bookmark -- figure out how to save
            self.detailsForm.urlBox.setText(new_url)
