# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/pocket_import.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(516, 376)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.includeTagCheck = QtWidgets.QCheckBox(self.groupBox_2)
        self.includeTagCheck.setObjectName("includeTagCheck")
        self.horizontalLayout_2.addWidget(self.includeTagCheck)
        self.includeTagBox = QtWidgets.QLineEdit(self.groupBox_2)
        self.includeTagBox.setObjectName("includeTagBox")
        self.horizontalLayout_2.addWidget(self.includeTagBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.includeFavoritesCheck = QtWidgets.QCheckBox(self.groupBox_2)
        self.includeFavoritesCheck.setObjectName("includeFavoritesCheck")
        self.verticalLayout.addWidget(self.includeFavoritesCheck)
        self.incrementalSyncCheck = QtWidgets.QCheckBox(self.groupBox_2)
        self.incrementalSyncCheck.setObjectName("incrementalSyncCheck")
        self.verticalLayout.addWidget(self.incrementalSyncCheck)
        self.verticalLayout_3.addWidget(self.groupBox_2)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.copyExcerptCheck = QtWidgets.QCheckBox(self.groupBox)
        self.copyExcerptCheck.setObjectName("copyExcerptCheck")
        self.verticalLayout_2.addWidget(self.copyExcerptCheck)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tagImportsCheck = QtWidgets.QCheckBox(self.groupBox)
        self.tagImportsCheck.setObjectName("tagImportsCheck")
        self.horizontalLayout_3.addWidget(self.tagImportsCheck)
        self.tagImportsBox = QtWidgets.QLineEdit(self.groupBox)
        self.tagImportsBox.setObjectName("tagImportsBox")
        self.horizontalLayout_3.addWidget(self.tagImportsBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.copyTagsCheck = QtWidgets.QCheckBox(self.groupBox)
        self.copyTagsCheck.setObjectName("copyTagsCheck")
        self.verticalLayout_2.addWidget(self.copyTagsCheck)
        self.discardTagsCheck = QtWidgets.QCheckBox(self.groupBox)
        self.discardTagsCheck.setObjectName("discardTagsCheck")
        self.verticalLayout_2.addWidget(self.discardTagsCheck)
        self.discardTagsBox = QtWidgets.QLineEdit(self.groupBox)
        self.discardTagsBox.setObjectName("discardTagsBox")
        self.verticalLayout_2.addWidget(self.discardTagsBox)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.importButton = QtWidgets.QPushButton(Dialog)
        self.importButton.setObjectName("importButton")
        self.horizontalLayout.addWidget(self.importButton)
        self.cancelButton = QtWidgets.QPushButton(Dialog)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Pocket Import Options"))
        self.groupBox_2.setTitle(_translate("Dialog", "Article selection"))
        self.includeTagCheck.setText(_translate("Dialog", "Include only items with the Pocket &tag:"))
        self.includeFavoritesCheck.setText(_translate("Dialog", "Include only &favorites"))
        self.incrementalSyncCheck.setText(_translate("Dialog", "Include only &items changed since the last successful import"))
        self.groupBox.setTitle(_translate("Dialog", "Import settings"))
        self.copyExcerptCheck.setText(_translate("Dialog", "Copy Pocket item e&xcerpt to RabbitMark description field"))
        self.tagImportsCheck.setText(_translate("Dialog", "Tag imported items with the Rabbit&Mark tag:"))
        self.copyTagsCheck.setText(_translate("Dialog", "Pocket ta&gs become RabbitMark tags"))
        self.discardTagsCheck.setText(_translate("Dialog", "&Discard the following tags (comma-separated):"))
        self.importButton.setText(_translate("Dialog", "&Next >"))
        self.cancelButton.setText(_translate("Dialog", "&Cancel"))

