"""
utils.py - Qt GUI and other utility functions

(These should be split up in another refactor round in the future.)
"""

from enum import Enum, unique
from typing import Any, Dict, Tuple

# Yet again, pylint can't seem to read PyQt5's module structure properly...
# pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMessageBox, QInputDialog

NOTAGS = "(no tags)"
DATE_FORMAT = '%Y-%m-%d'

@unique
class SearchMode(Enum):
    Or = 0
    And = 1

def informationBox(text, title=None) -> None:
    """
    Message box with the information icon and an OK button.
    """
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(QMessageBox.Information)
    if title:
        msgBox.setWindowTitle(title)
    msgBox.exec_()

def errorBox(text, title=None) -> None:
    """
    Message box with the error icon and an OK button.
    """
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(QMessageBox.Critical)
    if title:
        msgBox.setWindowTitle(title)
    msgBox.exec_()

def warningBox(text, title=None) -> None:
    """
    Message box with the warning icon and an OK button.
    """
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(QMessageBox.Warning)
    if title:
        msgBox.setWindowTitle(title)
    msgBox.exec_()

def questionBox(text, title=None):
    """
    Message box with the question icon and Yes and No buttons.

    Returns QMessageBox.Yes if yes was pushed, QMessageBox.No if no was pushed.
    QMessageBox is PyQt4.QtGui.QMessageBox if you need to import it to use
    those constants.
    """
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    if title:
        msgBox.setWindowTitle(title)
    return msgBox.exec_()


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
        'tags': [i.strip() for i in
                 str(detailsForm.tagsBox.text()).split(',')
                 if i.strip() != ''],
    }
