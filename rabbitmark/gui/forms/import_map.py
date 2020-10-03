# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/import_map.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(824, 464)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mappingTable = QtWidgets.QTableWidget(Dialog)
        self.mappingTable.setMaximumSize(QtCore.QSize(400, 16777215))
        self.mappingTable.setAlternatingRowColors(True)
        self.mappingTable.setObjectName("mappingTable")
        self.mappingTable.setColumnCount(0)
        self.mappingTable.setRowCount(0)
        self.mappingTable.horizontalHeader().setDefaultSectionSize(180)
        self.mappingTable.horizontalHeader().setStretchLastSection(True)
        self.mappingTable.verticalHeader().setVisible(False)
        self.horizontalLayout_2.addWidget(self.mappingTable)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.previewWidget = QtWidgets.QWidget(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.previewWidget.sizePolicy().hasHeightForWidth())
        self.previewWidget.setSizePolicy(sizePolicy)
        self.previewWidget.setObjectName("previewWidget")
        self.verticalLayout.addWidget(self.previewWidget)
        self.horizontalLayout_2.addWidget(self.groupBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.statusLabel = QtWidgets.QLabel(Dialog)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.horizontalLayout.addWidget(self.statusLabel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.importButton = QtWidgets.QPushButton(Dialog)
        self.importButton.setObjectName("importButton")
        self.horizontalLayout.addWidget(self.importButton)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "Preview"))
        self.importButton.setText(_translate("Dialog", "&Import"))
        self.cancelButton.setText(_translate("Dialog", "&Cancel"))

