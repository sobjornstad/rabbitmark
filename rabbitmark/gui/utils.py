"""
utils.py - Qt GUI and other utility functions

(These should be split up in another refactor round in the future.)
"""

from contextlib import contextmanager
import os
from typing import Any, Dict, Tuple

# Yet again, pylint can't seem to read PyQt5's module structure properly...
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMessageBox, QInputDialog


def _box(text: str, title: str, icon: QMessageBox.Icon) -> QMessageBox:
    "Helper function to do most of the work of setting up a standard message box."
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(icon)
    if title:
        msgBox.setWindowTitle(title)
    return msgBox


def informationBox(text, title=None) -> None:
    "Show a message box with the information icon and an OK button."
    _box(text, title, QMessageBox.Information).exec_()


def errorBox(text, title=None) -> None:
    "Show a message box with the error icon and an OK button."
    _box(text, title, QMessageBox.Critical).exec_()


def warningBox(text, title=None) -> None:
    "Show a message box with the warning icon and an OK button."
    _box(text, title, QMessageBox.Warning).exec_()


def questionBox(text, title=None) -> bool:
    """
    Show a message box with the question icon and Yes and No buttons.

    Returns True if yes pushed, False if no.
    """
    msgBox = _box(text, title, QMessageBox.Question)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    return msgBox.exec_() == QMessageBox.Yes


def inputBox(label, title=None, defaultText=None) -> Tuple[str, bool]:
    """
    Basic input box. Returns a tuple:
        [0] The text entered, as a Unicode string.
        [1] True if dialog accepted, False if rejected.

    See also passwordEntry().
    """
    if defaultText is not None:
        ret = QInputDialog.getText(None, title, label, text=defaultText)
    else:
        ret = QInputDialog.getText(None, title, label)
    return str(ret[0]), ret[1]


def mark_dictionary(detailsForm) -> Dict[str, Any]:
    """
    Given a details form object, return a dictionary of its content
    in the format needed by bookmark.save_if_edited().
    """
    return {
        'name': str(detailsForm.nameBox.text()),
        'url': str(detailsForm.urlBox.text()),
        'description': str(detailsForm.descriptionBox.toPlainText()),
        'private': detailsForm.privateCheck.isChecked(),
        'skip_linkcheck': detailsForm.linkcheckCheck.isChecked(),
        'tags': [i.strip() for i in
                 str(detailsForm.tagsBox.text()).split(',')
                 if i.strip() != ''],
    }

def forceExtension(filename, ext):
    """
    On Linux, a filename extension might not be automatically appended to the
    result of a file open/save box. This means we have to do it ourselves and
    check to be sure we're not overwriting something ourselves.

    This check is not safe from race conditions (if another program wrote a
    file with the same name between this function running and the output
    routine, the other file would be overwritten), but the chance of that
    causing a bad problem are essentially zero in this situation, and
    neither is the normal file-save routine.

    Arguments:
        filename: the path to (or simple name of) the file we're checking
        ext: the extension, without period, you want to ensure is included

    Return:
      - The filename (modified or not) if the file does not exist;
      - None if it does exist and the user said she didn't want to
        overwrite it.

    Originally taken from Tabularium <https://github.com/sobjornstad/tabularium>.
    """
    # on linux, the extension might not be automatically appended
    if not filename.endswith('.%s' % ext):
        filename += ".%s" % ext
        if os.path.exists(filename):
            r = questionBox("%s already exists.\nDo you want to "
                            "replace it?" % filename)
            if r != QMessageBox.Yes: # yes
                return None
    return filename

@contextmanager
def signalsBlocked(widget):
    "Context manager to block signals on a widget /widget/, then restore the old value."
    old_value = widget.blockSignals(True)
    yield
    widget.blockSignals(old_value)
