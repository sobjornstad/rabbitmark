"""
wayback_search_dialog.py -- interface for searching the WayBackMachine
"""

from typing import Optional, List

# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import pyqtSignal, QThread, QUrl

from .librm import bookmark
from .librm import config
from .librm import pocket

from .forms.pocket_import import Ui_Dialog as Ui_PocketImportDialog
from . import utils


class PocketImportDialog(QDialog):
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
        new_items = pocket.sync_items(
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
        from pprint import pprint; pprint(new_items)
        #TODO: Do something
        print("Accepted the dialog")
        super().accept()
