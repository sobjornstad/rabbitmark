# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/linkcheck_progress.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(515, 395)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.progressBar = QtWidgets.QProgressBar(Dialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.okLabel = QtWidgets.QLabel(Dialog)
        self.okLabel.setObjectName("okLabel")
        self.horizontalLayout.addWidget(self.okLabel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.failedLabel = QtWidgets.QLabel(Dialog)
        self.failedLabel.setObjectName("failedLabel")
        self.horizontalLayout.addWidget(self.failedLabel)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.totalLabel = QtWidgets.QLabel(Dialog)
        self.totalLabel.setObjectName("totalLabel")
        self.horizontalLayout.addWidget(self.totalLabel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem2 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem2)
        self.progressLog = QtWidgets.QPlainTextEdit(Dialog)
        self.progressLog.setObjectName("progressLog")
        self.verticalLayout.addWidget(self.progressLog)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Find Broken Links"))
        self.label.setText(_translate("Dialog", "RabbitMark is sniffing your database for link rot. This may take a few minutes."))
        self.okLabel.setText(_translate("Dialog", "OK: 0"))
        self.failedLabel.setText(_translate("Dialog", "Failed: 0"))
        self.totalLabel.setText(_translate("Dialog", "Total: 2"))
        self.cancelButton.setText(_translate("Dialog", "&Cancel"))

