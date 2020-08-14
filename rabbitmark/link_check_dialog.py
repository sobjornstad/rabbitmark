"""
wayback_search_dialog.py -- interface for searching the WayBackMachine
"""

from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from .librm.bookmark import get_bookmark_by_id

from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from .forms.linkcheck import Ui_Dialog as Ui_LinkCheckDialog
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

    def updateDetailsPane(self):
        """
        Fill the editor/details pane with data from the currently selected bookmark.
        """
        sfdw = self.detailsForm

        blink_obj = self.blinks[self.form.pageList.selectedItems()[0].text()]
        mark = get_bookmark_by_id(self.session, blink_obj.pk)

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