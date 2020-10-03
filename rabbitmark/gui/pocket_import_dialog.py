"""
wayback_search_dialog.py -- interface for searching the WayBackMachine
"""

from typing import Optional, List

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices, QCursor
from PyQt5.QtCore import pyqtSignal, QThread, QUrl, Qt

from ..librm import bookmark
from ..librm import config
from ..librm import pocket

from .forms.bookmark_details import Ui_Form as BookmarkDetailsWidget
from .forms.pocket_import import Ui_Dialog as Ui_PocketImportDialog
from .forms.pocket_preview import Ui_Dialog as Ui_PocketPreviewDialog
from . import utils


class PocketSettingsDialog(QDialog):
    """
    Choose settings for importing from Pocket.
    """
    def __init__(self, parent, session) -> None:
        "Set up the dialog."
        QDialog.__init__(self)
        self.form = Ui_PocketImportDialog()
        self.form.setupUi(self)
        self.parent = parent
        self.session = session

        self.persistence_layer_map = {
            "pocket_dlg_str_syncTag": self.form.includeTagBox,
            "pocket_dlg_bool_favoritesOnly": self.form.includeFavoritesCheck,
            "pocket_dlg_bool_incrementalSync": self.form.incrementalSyncCheck,
            "pocket_dlg_bool_excerptAsDescription": self.form.copyExcerptCheck,
            "pocket_dlg_bool_copyTags": self.form.copyTagsCheck,
            "pocket_dlg_str_discardTags": self.form.discardTagsBox,
            "pocket_dlg_str_tagWith": self.form.tagImportsBox,
        }
        self.default_options = {
            "pocket_dlg_str_syncTag": "",
            "pocket_dlg_bool_favoritesOnly": False,
            "pocket_dlg_bool_incrementalSync": True,
            "pocket_dlg_bool_excerptAsDescription": False,
            "pocket_dlg_bool_copyTags": False,
            "pocket_dlg_str_discardTags": "",
            "pocket_dlg_str_tagWith": "",
        }

        self.form.importButton.clicked.connect(self.accept)
        self.form.cancelButton.clicked.connect(self.reject)

        self._populate_dialog()

    def _populate_dialog(self):
        for name, obj in self.persistence_layer_map.items():
            if '_str_' in name:
                cur = config.get(self.session, name)
                if cur is None:
                    obj.setText(self.default_options[name])
                else:
                    obj.setText(cur)
            elif '_bool_' in name:
                cur = config.get(self.session, name)
                if cur is None:
                    cur = self.default_options[name]
                elif cur == "False":
                    cur = False
                elif cur == "True":
                    cur = True
                else:
                    raise AssertionError(f"Invalid value for {name}: {cur}")
                obj.setChecked(cur)
            else:
                raise AssertionError("Improperly typed configuration field!")

        if self.form.discardTagsBox.text():
            self.form.discardTagsCheck.setChecked(True)
        if self.form.includeTagBox.text():
            self.form.includeTagCheck.setChecked(True)
        if self.form.tagImportsBox.text():
            self.form.tagImportsCheck.setChecked(True)

        def _line_facet(is_checked, dependent_widget):
            """
            If a line edit's parent is unchecked, disable and clear it.
            If rechecked, enable it and put the focus there to enter a value.
            """
            dependent_widget.setEnabled(is_checked)
            if is_checked:
                dependent_widget.setFocus()
            else:
                dependent_widget.clear()

        def _check_facet(is_checked, dependent_widget):
            "If a checkbox's parent is unchecked, disable and unset the dependency."
            dependent_widget.setEnabled(is_checked)
            if not is_checked:
                dependent_widget.setChecked(False)

        def _widget_dependency(conditional_widget, dependent_widget, facet):
            """
            Configure a dependency between two widgets, so that when the
            /conditional_widget/ (a checkable item) is not checked, the
            /dependent_widget/ (any item) is disabled and blanked.

            In order to support different types of dependent_widgets, the
            third argument, /facet/, is used. The facet is a callable that
            takes a boolean (whether the conditional_widget is now checked)
            and the dependent widget, and updates the dependent widget to the
            correct state.

            When you configure the dependency, the enablement is immediately
            updated to match the current value of conditional_widget. In
            addition, a signal is configured to keep them in line in the
            future.

            Cascading/recursive dependencies are supported via the signal
            mechanism; just be sure to configure the lowest-level dependency
            first, and higher-level ones afterwards in topological order.
            """
            wrapped = lambda state: facet(state, dependent_widget)
            conditional_widget.toggled.connect(wrapped)
            wrapped(conditional_widget.isChecked())

        sf = self.form
        _widget_dependency(sf.includeTagCheck, sf.includeTagBox, _line_facet)
        _widget_dependency(sf.discardTagsCheck, sf.discardTagsBox, _line_facet)
        _widget_dependency(sf.copyTagsCheck, sf.discardTagsCheck, _check_facet)
        _widget_dependency(sf.tagImportsCheck, sf.tagImportsBox, _line_facet)

    def _save_fields(self):
        for name, obj in self.persistence_layer_map.items():
            if '_str_' in name:
                cur = config.put(self.session, name, obj.text())
            elif '_bool_' in name:
                cur = config.put(self.session, name, str(obj.isChecked()))
            else:
                raise AssertionError("Improperly typed configuration field!")
        self.session.commit()


    def accept(self):
        self._save_fields()
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            success, result = pocket.sync_items(
                session=self.session,
                pconf=pocket.PocketConfig(self.session),
                get_only_tag = self.form.includeTagBox.text(),
                get_only_favorites=self.form.includeFavoritesCheck.isChecked(),
                get_only_since=self.form.incrementalSyncCheck.isChecked(),
                use_excerpt=self.form.copyExcerptCheck.isChecked(),
                tag_with=self.form.tagImportsBox.text(),
                tag_passthru=self.form.copyTagsCheck.isChecked(),
                discard_pocket_tags=self.form.discardTagsBox.text(),
            )
            if success:
                self.items = result
            else:
                utils.errorBox(result, title="Error syncing with Pocket.")
        finally:
            QApplication.restoreOverrideCursor()

        if not self.items:
            utils.warningBox("No matching articles found. "
                             "Please try different criteria.")
        else:
            super().accept()



class PocketArticleDialog(QDialog):
    """
    Select specific Pocket articles to import.
    """
    def __init__(self, parent, session, item_list) -> None:
        "Set up the dialog."
        QDialog.__init__(self)
        self.form = Ui_PocketPreviewDialog()
        self.form.setupUi(self)
        self.parent = parent
        self.session = session
        self.items = {i['name']: i for i in item_list}
        self.went_back = False

        # set up details widget
        self.detailsForm = BookmarkDetailsWidget()
        self.detailsForm.setupUi(self.form.detailsWidget)
        self.detailsForm.browseUrlButton.clicked.connect(self.onBrowseUrl)
        self.detailsForm.copyUrlButton.clicked.connect(self.onCopyUrl)
        sfdw = self.detailsForm
        for i in (sfdw.nameBox, sfdw.urlBox, sfdw.tagsBox, sfdw.descriptionBox):
            i.setReadOnly(True)
        for i in (sfdw.privateCheck, sfdw.linkcheckCheck):
            i.setEnabled(False)

        self.form.importButton.clicked.connect(self.accept)
        self.form.cancelButton.clicked.connect(self.reject)
        self.form.backButton.clicked.connect(self.onBack)
        self.form.importOneButton.clicked.connect(self.onImportOne)
        self.form.importAllButton.clicked.connect(self.onImportAll)
        self.form.skipOneButton.clicked.connect(self.onSkipOne)
        self.form.skipAllButton.clicked.connect(self.onSkipAll)
        self.form.importList.currentItemChanged.connect(self.onImportSelectChanged)

        for item in self.items.values():
            if bookmark.url_exists(self.session, item['url']):
                self.form.skipList.addItem(item['name'])
            else:
                self.form.importList.addItem(item['name'])
        if self.form.skipList.count():
            ess = '' if self.form.skipList.count() == 1 else 's'
            utils.informationBox(
                f"{self.form.skipList.count()} item{ess} were placed on the skip list "
                f"because you already have a bookmark with the same URL.")

    def accept(self):
        for list_item in self.form.importList.findItems('.*', Qt.MatchRegExp):
            item = self.items[list_item.text()]
            bookmark.add_bookmark(self.session, **item)
        self.session.commit()
        super().accept()
        utils.informationBox(f"{self.form.importList.count()} items imported.")

    def onBack(self) -> None:
        self.went_back = True
        self.reject()

    def onBrowseUrl(self) -> None:
        QDesktopServices.openUrl(QUrl(self.detailsForm.urlBox.text()))

    def onCopyUrl(self) -> None:
        QApplication.clipboard().setText(self.detailsForm.urlBox.text())

    def onImportOne(self) -> None:
        item = self.form.skipList.takeItem(self.form.skipList.currentRow())
        self.form.importList.addItem(item)

    def onImportAll(self) -> None:
        with utils.signalsBlocked(self.form.importList):
            self.form.skipList.clear()
            self.form.importList.clear()
            self.form.importList.addItems(list(self.items.keys()))

    def onSkipOne(self) -> None:
        item = self.form.importList.takeItem(self.form.importList.currentRow())
        self.form.skipList.addItem(item)

    def onSkipAll(self) -> None:
        with utils.signalsBlocked(self.form.importList):
            self.form.importList.clear()
            self.form.skipList.clear()
            self.form.skipList.addItems(list(self.items.keys()))

    def onImportSelectChanged(self, new, _previous) -> None:
        sfdw = self.detailsForm
        item = self.items[new.text()]
        sfdw.nameBox.setText(item['name'])
        sfdw.urlBox.setText(item['url'])
        sfdw.descriptionBox.setPlainText(item['description'])
        tags = ', '.join(item['tags'])
        sfdw.tagsBox.setText(tags)

        # If a name or URL is too long to fit in the box, this will make
        # the box show the beginning of it rather than the end.
        for i in (sfdw.nameBox, sfdw.urlBox, sfdw.tagsBox):
            i.setCursorPosition(0)


def import_process(parent) -> bool:
    """
    Walk user through the process of importing with a two-step wizard.
    """
    dlg = PocketSettingsDialog(parent, parent.session)
    if not dlg.exec_():
        return False
    items = dlg.items

    dlg = PocketArticleDialog(parent, parent.session, items)
    if not dlg.exec_():
        if dlg.went_back:
            # try again from the start
            return import_process(parent)

    return True
