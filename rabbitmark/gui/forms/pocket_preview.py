# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/pocket_preview.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(637, 512)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
        self.skipList = QtWidgets.QListWidget(Dialog)
        self.skipList.setObjectName("skipList")
        self.gridLayout.addWidget(self.skipList, 1, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.importOneButton = QtWidgets.QPushButton(Dialog)
        self.importOneButton.setObjectName("importOneButton")
        self.verticalLayout.addWidget(self.importOneButton)
        self.skipOneButton = QtWidgets.QPushButton(Dialog)
        self.skipOneButton.setObjectName("skipOneButton")
        self.verticalLayout.addWidget(self.skipOneButton)
        self.importAllButton = QtWidgets.QPushButton(Dialog)
        self.importAllButton.setObjectName("importAllButton")
        self.verticalLayout.addWidget(self.importAllButton)
        self.skipAllButton = QtWidgets.QPushButton(Dialog)
        self.skipAllButton.setObjectName("skipAllButton")
        self.verticalLayout.addWidget(self.skipAllButton)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)
        self.importList = QtWidgets.QListWidget(Dialog)
        self.importList.setObjectName("importList")
        self.gridLayout.addWidget(self.importList, 1, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.detailsWidget = QtWidgets.QWidget(Dialog)
        self.detailsWidget.setObjectName("detailsWidget")
        self.verticalLayout_2.addWidget(self.detailsWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.backButton = QtWidgets.QPushButton(Dialog)
        self.backButton.setObjectName("backButton")
        self.horizontalLayout_2.addWidget(self.backButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.importButton = QtWidgets.QPushButton(Dialog)
        self.importButton.setObjectName("importButton")
        self.horizontalLayout_2.addWidget(self.importButton)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.label.setBuddy(self.skipList)
        self.label_2.setBuddy(self.importList)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Import Preview"))
        self.label.setText(_translate("Dialog", "&Skip"))
        self.label_2.setText(_translate("Dialog", "I&mport"))
        self.skipList.setSortingEnabled(True)
        self.importOneButton.setText(_translate("Dialog", ">"))
        self.skipOneButton.setText(_translate("Dialog", "<"))
        self.importAllButton.setText(_translate("Dialog", "All >>"))
        self.skipAllButton.setText(_translate("Dialog", "All <<"))
        self.importList.setSortingEnabled(True)
        self.backButton.setText(_translate("Dialog", "< &Back"))
        self.importButton.setText(_translate("Dialog", "&Import"))
        self.cancelButton.setText(_translate("Dialog", "&Cancel"))

