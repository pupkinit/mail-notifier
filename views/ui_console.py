# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources\console.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Console(object):
    def setupUi(self, Console):
        Console.setObjectName("Console")
        Console.resize(332, 231)
        Console.setMouseTracking(False)
        Console.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/mailbox_empty.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Console.setWindowIcon(icon)
        Console.setToolTip("")
        Console.setWhatsThis("")
        self.horizontalLayout = QtWidgets.QHBoxLayout(Console)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.logList = QtWidgets.QListWidget(Console)
        self.logList.setMinimumSize(QtCore.QSize(0, 0))
        self.logList.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.logList.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.logList.setAutoFillBackground(False)
        self.logList.setObjectName("logList")
        self.horizontalLayout.addWidget(self.logList)

        self.retranslateUi(Console)
        QtCore.QMetaObject.connectSlotsByName(Console)

    def retranslateUi(self, Console):
        _translate = QtCore.QCoreApplication.translate
        Console.setWindowTitle(_translate("Console", "Console"))


from views import resources_rc
