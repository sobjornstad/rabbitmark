"""
import_dialog.py -- interface for importing from a CSV file
"""

from typing import Optional

# pylint: disable=no-name-in-module
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QComboBox

from rabbitmark.librm import interchange

from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from .forms.import_map import Ui_Dialog as ImportMappingForm
from . import utils

DONT_MAP = "(Ignore)"


class MultipleResultsError(Exception):
    pass


class ImportDialog(QDialog):
    "Import bookmarks from a CSV file."
    def __init__(self, parent, session, target_path: str) -> None:
        "Set up the dialog."
        QDialog.__init__(self)
        self.form = ImportMappingForm()
        self.form.setupUi(self)
        self.parent = parent
        self.session = session
        self.target_path = target_path

        # set up details widget
        self.detailsForm = BookmarkDetailsWidget()
        self.detailsForm.setupUi(self.form.previewWidget)
        self.detailsForm.browseUrlButton.clicked.connect(self.onBrowseUrl)
        self.detailsForm.copyUrlButton.clicked.connect(self.onCopyUrl)
        sfdw = self.detailsForm
        for i in (sfdw.nameBox, sfdw.urlBox, sfdw.tagsBox, sfdw.descriptionBox):
            i.setReadOnly(True)
        for i in (sfdw.privateCheck, sfdw.linkcheckCheck):
            i.setEnabled(False)

        # set up buttons
        self.form.importButton.clicked.connect(self.accept)
        self.form.cancelButton.clicked.connect(self.reject)
        self.form.importButton.setEnabled(False)

        # set up mappings
        self.schema = interchange.get_csv_schema(self.target_path)
        self.setupMappingTable(self.schema)

    def setupMappingTable(self, schema) -> None:
        "Create the table allowing the user to map fields."
        self.form.mappingTable.setRowCount(len(schema.columns))
        self.form.mappingTable.setColumnCount(2)
        self.form.mappingTable.setHorizontalHeaderLabels(
            ["File column", "RabbitMark field"])
        available_fields = [DONT_MAP, "Name", "URL", "Tags", "Description"]

        for row_index, row_name in enumerate(schema.columns):
            file_col = QTableWidgetItem(row_name)
            file_col.setFlags(file_col.flags() ^ Qt.ItemIsEditable)

            rm_combo = QComboBox()
            rm_combo.addItems(available_fields)
            rm_combo.setCurrentIndex(0)
            rm_combo.currentIndexChanged.connect(self.onMappingChanged)

            self.form.mappingTable.setItem(row_index, 0, file_col)
            self.form.mappingTable.setCellWidget(row_index, 1, rm_combo)

        self._updatePreview()

    def _currentMappingOf(self, rm_fieldname: str) -> Optional[str]:
        """
        Return the CSV column name currently associated with the rm_fieldname,
        or None if there is no mapped field.

        Raises:
            MultipleResultsError - if there are multiple columns mapped to the
            same RabbitMark field.
        """
        matches = []
        for row in range(len(self.schema.columns)):
            item = self.form.mappingTable.cellWidget(row, 1)
            if item.currentText() == rm_fieldname:
                matches.append(self.form.mappingTable.item(row, 0).text())

        if not matches:
            return None
        elif len(matches) > 1:
            raise MultipleResultsError()
        else:
            return matches[0]

    def _updatePreview(self) -> None:
        """
        Change the preview section of the window to show a sample entry that
        will be created when import is successful.

        The result depends on how fields are currently mapped; the entire preview
        may be cleared if the new mapping is not valid.
        """
        def _get(field):
            mapping = self._currentMappingOf(field)
            return None if mapping is None else self.schema.first_data_row[mapping]

        def _set_fields(sfdw, name, url, description, tags):
            sfdw.nameBox.setText(name)
            sfdw.urlBox.setText(url)
            sfdw.descriptionBox.setPlainText(description or "")
            sfdw.tagsBox.setText(tags or "")
            sfdw.privateCheck.setChecked(False)
            sfdw.linkcheckCheck.setChecked(False)

        def _clear_fields(sfdw):
            _set_fields(sfdw, "", "", "", "")

        sfdw = self.detailsForm
        try:
            name = _get("Name")
            url = _get("URL")
            description = _get("Description")
            tags = _get("Tags")
        except MultipleResultsError:
            self.form.importButton.setEnabled(False)
            self.form.statusLabel.setText(
                "Only one column may be mapped to each RabbitMark field.")
            _clear_fields(sfdw)
            return

        if name is None or url is None:
            self.form.importButton.setEnabled(False)
            self.form.statusLabel.setText(
                "Please map at least the Name and URL fields.")
            _clear_fields(sfdw)
            return

        self.form.statusLabel.setText("")
        self.form.importButton.setEnabled(True)
        _set_fields(sfdw, name, url, description, tags)

        # If a name or URL is too long to fit in the box, this will make
        # the box show the beginning of it rather than the end.
        for i in (sfdw.nameBox, sfdw.urlBox, sfdw.tagsBox):
            i.setCursorPosition(0)

    def accept(self):
        "Import bookmarks and close dialog."
        mapping = []
        for table_rownum in range(len(self.schema.columns)):
            rm_field = self.form.mappingTable.cellWidget(table_rownum, 1).currentText()
            mapping.append(None if rm_field == DONT_MAP else rm_field)

        imported, duplicated = interchange.import_bookmarks_from_csv(
            session=self.session,
            target_path=self.target_path,
            dialect=self.schema.dialect,
            mapping=mapping)
        self.session.commit()

        super().accept()
        msg = f"{imported} bookmark{'' if imported == 1 else 's'} imported."
        if duplicated > 0:
            ess = '' if duplicated == 1 else 's'
            msg += (f" {duplicated} bookmark{ess} "
                    f"with URL{ess} already in collection ignored.")
        utils.informationBox(msg)

    def onMappingChanged(self, _new_index) -> None:
        self._updatePreview()

    def onBrowseUrl(self) -> None:
        QDesktopServices.openUrl(QUrl(self.detailsForm.urlBox.text()))

    def onCopyUrl(self) -> None:
        QApplication.clipboard().setText(self.detailsForm.urlBox.text())
