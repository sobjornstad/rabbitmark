# -* coding: utf-8 *-
# Copyright 2015 Soren Bjornstad. All rights reserved.

"""
Largely copied from Personal Indexer.
"""

from PyQt5.QtWidgets import QDialog, QMessageBox, QInputDialog, QLineEdit

def informationBox(text, title=None):
    """
    Message box with the information icon and an OK button.
    """
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(QMessageBox.Information)
    if title:
        msgBox.setWindowTitle(title)
    msgBox.exec_()

def errorBox(text, title=None):
    """
    Message box with the error icon and an OK button.
    """
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(QMessageBox.Critical)
    if title:
        msgBox.setWindowTitle(title)
    msgBox.exec_()

def warningBox(text, title=None):
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


def inputBox(label, title=None, defaultText=None):
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
