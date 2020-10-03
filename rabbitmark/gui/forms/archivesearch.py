# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/archivesearch.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(525, 305)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.snapshotLabel = QtWidgets.QLabel(Dialog)
        self.snapshotLabel.setObjectName("snapshotLabel")
        self.verticalLayout_3.addWidget(self.snapshotLabel)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.urlBox = QtWidgets.QLineEdit(Dialog)
        self.urlBox.setReadOnly(True)
        self.urlBox.setObjectName("urlBox")
        self.horizontalLayout.addWidget(self.urlBox)
        self.copyButton = QtWidgets.QPushButton(Dialog)
        self.copyButton.setObjectName("copyButton")
        self.horizontalLayout.addWidget(self.copyButton)
        self.browseButton = QtWidgets.QPushButton(Dialog)
        self.browseButton.setObjectName("browseButton")
        self.horizontalLayout.addWidget(self.browseButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.stateLabel = QtWidgets.QLabel(Dialog)
        self.stateLabel.setObjectName("stateLabel")
        self.verticalLayout_3.addWidget(self.stateLabel)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.useRadio = QtWidgets.QRadioButton(self.groupBox)
        self.useRadio.setObjectName("useRadio")
        self.verticalLayout.addWidget(self.useRadio)
        self.newerRadio = QtWidgets.QRadioButton(self.groupBox)
        self.newerRadio.setObjectName("newerRadio")
        self.verticalLayout.addWidget(self.newerRadio)
        self.olderRadio = QtWidgets.QRadioButton(self.groupBox)
        self.olderRadio.setObjectName("olderRadio")
        self.verticalLayout.addWidget(self.olderRadio)
        self.backupRadio = QtWidgets.QRadioButton(self.groupBox)
        self.backupRadio.setObjectName("backupRadio")
        self.verticalLayout.addWidget(self.backupRadio)
        self.cancelRadio = QtWidgets.QRadioButton(self.groupBox)
        self.cancelRadio.setObjectName("cancelRadio")
        self.verticalLayout.addWidget(self.cancelRadio)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setAutoDefault(False)
        self.okButton.setDefault(True)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout_2.addWidget(self.okButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "WayBackMachine Search"))
        self.snapshotLabel.setText(_translate("Dialog", "Please try the following snapshot:"))
        self.copyButton.setText(_translate("Dialog", "Copy"))
        self.copyButton.setShortcut(_translate("Dialog", "Ctrl+Shift+C"))
        self.browseButton.setText(_translate("Dialog", "Browse to"))
        self.browseButton.setShortcut(_translate("Dialog", "Ctrl+B"))
        self.stateLabel.setText(_translate("Dialog", "There are 3 older and 6 newer snapshots.\n"
"How do you want to proceed?"))
        self.useRadio.setText(_translate("Dialog", "&Use this snapshot as this site\'s URL in my database"))
        self.newerRadio.setText(_translate("Dialog", "Try a &newer snapshot (this one works, but seems outdated)"))
        self.olderRadio.setText(_translate("Dialog", "Try an &older snapshot (this one doesn\'t work)"))
        self.backupRadio.setText(_translate("Dialog", "&Back up to the last snapshot and increase search range"))
        self.cancelRadio.setText(_translate("Dialog", "&Cancel and keep the original URL"))
        self.okButton.setText(_translate("Dialog", "OK"))

