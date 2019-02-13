#!/usr/bin/env python3

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QLineEdit,
                             QMessageBox, QMenu, QSystemTrayIcon, QInputDialog)
from PyQt5.QtCore import (QTimer, QSettings)
import imaplib
import email

import subprocess
from views.ui_settings import Ui_Settings
from views.ui_about import Ui_about
from views.ui_details import Ui_Details
from views.ui_console import Ui_Console
from PyQt5 import QtCore, QtGui, QtWidgets
import socket
from datetime import datetime, time

imaplib._MAXLINE = 400000
# variables
programTitle = "Mail Notifier"
programVersion = "3.01-dev"
settings = QSettings("settings.conf", QSettings.IniFormat)


def GlobalSettingsExist():
    if (settings.contains("CheckInterval") and settings.value("CheckInterval") != "" and
            settings.contains("Notify") and settings.value("Notify") != ""):
        return True
    else:
        return False


def AccountExist():
    groups = settings.childGroups()
    if len(groups) != 0:
        settings.beginGroup(groups[0])
        if (settings.contains("MailServer") and settings.value("MailServer") != "" and
                settings.contains("Port") and settings.value("Port") != "" and
                settings.contains("Login") and settings.value("Login") != "" and
                settings.contains("Password") and settings.value("Password") != "" and
                settings.contains("SSL") and settings.value("SSL") != ""):
            n = True
        else:
            n = False
        settings.endGroup()
    else:
        n = False
    if n:
        return True
    else:
        return False


class Window(QDialog):
    def __init__(self):
        super(Window, self).__init__()

        # UI
        self.createActions()
        self.setTitle = programTitle
        self.createTrayIcon()
        # Draw system tray icon
        pixmap = QtGui.QPixmap(QtGui.QPixmap(":icons/mailbox_empty.png"))
        self.trayIcon.setIcon(QtGui.QIcon(pixmap))
        # End drawing system tray icon

        self.trayIcon.setToolTip("You have no unread letters")
        self.trayIcon.show()

        # setup settings
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.SettingsRestore()

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.btnOK_clicked)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.btnCancel_clicked)
        self.ui.btnTestConnection.clicked.connect(self.btnTestConnection_clicked)
        self.ui.comboAccounts.currentTextChanged.connect(self.comboAccounts_changed)
        self.ui.btnAddAccount.clicked.connect(self.btnAddAccount_clicked)
        self.ui.btnRenameAccount.clicked.connect(self.btnRenameAccount_clicked)
        self.ui.btnSaveAccount.clicked.connect(self.btnSaveAccount_clicked)
        self.ui.btnRemoveAccount.clicked.connect(self.btnRemoveAccount_clicked)

        # Check if account doesn't exist, it creates default one
        if not AccountExist():
            self.ui.comboAccounts.addItem("Default")
            self.ui.comboAccounts.setCurrentText("Default")

        # Main timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(mail_check)

        self.lastCheckCount = 0  # variable for prevent annoying popup notification when mail count didn't change since last check

        # Menu actions

    def createActions(self):
        self.detailsShow = QAction(QIcon(':icons/details.png'), "&Details...", self, triggered=self.detailsShow)
        self.aboutShow = QAction(QIcon(':icons/mailbox_empty.png'), "&About " + programTitle + "...", self,
                                 triggered=self.aboutShow)
        self.checkNow = QAction(QIcon(':icons/check_now.png'), "&Check now", self, triggered=mail_check)
        self.restoreAction = QAction(QIcon(":icons/settings.png"), "&Settings...", self, triggered=self.showNormal)
        self.consoleAction = QAction(QIcon(":icons/logs.png"), "Conso&le...", self, triggered=self.consoleShow)
        self.quitAction = QAction(QIcon(':icons/menu_quit.png'), "&Quit", self, triggered=self.quit)

        # UI functions

    def quit(self):
        self.trayIcon.hide()
        QApplication.instance().quit()

    def createTrayIcon(self):
        self.trayIconMenu = QMenu(self)
        f = self.trayIconMenu.font()
        f.setBold(True)
        self.detailsShow.setFont(f)
        self.trayIconMenu.addAction(self.detailsShow)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.checkNow)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addAction(self.consoleAction)
        self.trayIconMenu.addAction(self.aboutShow)
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.activated.connect(self.trayIconActivated)

    def SettingsRestore(self):
        if GlobalSettingsExist() and AccountExist():
            groups = settings.childGroups()
            self.ui.comboAccounts.clear()  # Clear account items before fill them again
            for i in range(len(groups)):
                self.ui.comboAccounts.addItem(groups[i])
                self.ui.comboAccounts.setCurrentText(groups[i])
                settings.beginGroup(groups[i])
                self.ui.txtboxMailServer.setText(settings.value("MailServer"))
                self.ui.txtboxPort.setText(settings.value("Port"))
                self.ui.txtboxLogin.setText(settings.value("Login"))
                self.ui.txtboxPassword.setText(settings.value("Password"))
                self.ui.boolifSSL.setChecked(bool(settings.value("SSL")))
                settings.endGroup()
            if self.ui.comboAccounts.count() == 0:
                self.ui.comboAccounts.addItem("Default")
                self.ui.comboAccounts.setCurrentText("Default")
            self.ui.checkFreq.setValue(int(settings.value("CheckInterval")))
            self.ui.boolifNotify.setChecked(bool(settings.value("Notify")))

    def SettingsSave(self, account):
        settings.setValue("CheckInterval", self.ui.checkFreq.value())
        settings.setValue("Notify", self.ui.boolifNotify.isChecked())
        settings.beginGroup(account)
        settings.setValue("MailServer", self.ui.txtboxMailServer.text())
        settings.setValue("Port", self.ui.txtboxPort.text())
        settings.setValue("Login", self.ui.txtboxLogin.text())
        settings.setValue("Password", self.ui.txtboxPassword.text())
        settings.setValue("SSL", self.ui.boolifSSL.isChecked())
        settings.endGroup()

    def SettingsRemove(self, group):
        settings.beginGroup(group)
        settings.remove("")
        settings.endGroup()

    def btnOK_clicked(self):
        self.SettingsSave(self.ui.comboAccounts.currentText())

        if settings.value("MailServer") == "" or settings.value("Port") == "" or settings.value(
                "Login") == "" or settings.value("Password") == "":
            QMessageBox.critical(self, "Warning", "You should fill all fields in IMAP settings!")
            self.show()
        mail_check()
        self.ui.lblTestOutput.setText("")
        self.stop()
        self.start()

    def btnCancel_clicked(self):
        self.SettingsRestore()
        self.ui.lblTestOutput.setText("")

    def btnTestConnection_clicked(self):
        try:
            Mail(self.ui.txtboxMailServer.text(), self.ui.txtboxPort.text(), self.ui.boolifSSL.isChecked, self.ui.txtboxLogin.text(), self.ui.txtboxPassword.text())
            output = "Connection was established successfully"
        except:
            output = "Unable to establish connection to mailbox"
        finally:
            self.ui.lblTestOutput.setText(output)

    def btnAddAccount_clicked(self):
        GroupName = QInputDialog.getText(self, "Enter account name", "Enter account name", QLineEdit.Normal, "")
        if GroupName[0]:
            self.ui.comboAccounts.addItem(GroupName[0])
            self.ui.comboAccounts.setCurrentText(GroupName[0])

    def btnRenameAccount_clicked(self):
        Index = self.ui.comboAccounts.currentIndex()
        OldGroupName = self.ui.comboAccounts.currentText()
        GroupName = QInputDialog.getText(self, "Enter account name", "Enter account name", QLineEdit.Normal,
                                         self.ui.comboAccounts.currentText())
        if GroupName[0]:
            self.SettingsSave(GroupName[0])
            self.ui.comboAccounts.setItemText(Index, GroupName[0])
            self.ui.comboAccounts.setCurrentText(GroupName[0])
            self.SettingsRemove(OldGroupName)

    def btnSaveAccount_clicked(self):
        self.SettingsSave(self.ui.comboAccounts.currentText())
        self.ui.lblTestOutput.setText("Account saved")

    def btnRemoveAccount_clicked(self):
        reply = QMessageBox.warning(self, 'Warning!', "Delete this account permanently?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            Index = self.ui.comboAccounts.currentIndex()
            GroupName = self.ui.comboAccounts.currentText()
            self.ui.comboAccounts.removeItem(Index)
            self.SettingsRemove(GroupName)
        # Check if account doesn't exist, it creates default one
        if not AccountExist():
            self.ui.comboAccounts.addItem("Default")
            self.ui.comboAccounts.setCurrentText("Default")

    def comboAccounts_changed(self):
        self.ui.lblTestOutput.setText("")
        settings.beginGroup(self.ui.comboAccounts.currentText())
        self.ui.txtboxMailServer.setText(settings.value("MailServer"))
        self.ui.txtboxPort.setText(settings.value("Port"))
        self.ui.txtboxLogin.setText(settings.value("Login"))
        self.ui.txtboxPassword.setText(settings.value("Password"))
        self.ui.boolifSSL.setChecked(bool(settings.value("SSL")))
        settings.endGroup()

    def aboutShow(self):
        if about.isMinimized:
            about.hide()
        about.show()
        about.activateWindow()

    def detailsShow(self):
        details.show()
        details.activateWindow()

    def consoleShow(self):
        console.show()
        console.activateWindow()

    def trayIconActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            details.show()
            details.activateWindow()

    def start(self):
        if GlobalSettingsExist() and AccountExist():
            CheckInterval = 1000 * 60 * int(settings.value("CheckInterval"))
        else:
            CheckInterval = 1000 * 60 * 5
        self.timer.setInterval(CheckInterval)
        self.timer.start()

    def stop(self):
        self.timer.stop()


class About(QDialog):
    def __init__(self):
        super(About, self).__init__()

        self.ui = Ui_about()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setFixedSize(511, 334)

        self.ui.lblNameVersion.setText(programTitle + " " + programVersion)

        f = QtCore.QFile(":/LICENSE.txt")
        if f.open(QtCore.QIODevice.ReadOnly | QtCore.QFile.Text):
            text = QtCore.QTextStream(f).readAll()
            f.close()
        self.ui.txtLicense.setPlainText(text)

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class Console(QDialog):
    def __init__(self):
        super(Console, self).__init__()

        self.ui = Ui_Console()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.Tool)
        if settings.contains("Console_width") and settings.contains("Console_height"):
            width = int(settings.value("Console_width"))
            height = int(settings.value("Console_height"))
            self.resize(width, height)

    def closeEvent(self, event):
        event.ignore()
        settings.setValue("Console_width", self.width())
        settings.setValue("Console_height", self.height())
        self.hide()

    def log(self, txt):
        self.ui.logList.addItem(datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S") + " - " + txt)


class Details(QDialog):
    def __init__(self):
        super(Details, self).__init__()

        self.ui = Ui_Details()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.Window)
        self.ui.btnRefresh.clicked.connect(self.Refresh_clicked)
        if settings.contains("Details_width") and settings.contains("Details_height"):
            width = int(settings.value("Details_width"))
            height = int(settings.value("Details_height"))
            self.resize(width, height)

    def closeEvent(self, event):
        event.ignore()
        settings.setValue("Details_width", self.width())
        settings.setValue("Details_height", self.height())
        self.hide()

    def Refresh_clicked(self):
        mail_check()


# Common functions

class Mail:
    def __init__(self, mailserver, port, ssl, user, password):
        socket.setdefaulttimeout(5)
        if ssl:
            self.imap = imaplib.IMAP4_SSL(mailserver, port)
        else:
            self.imap = imaplib.IMAP4(mailserver, port)
        # login to mailserver
        self.imap.login(user, password)

    def checkmail(self, account_name):
        # search unseen mails
        mails = []
        self.imap.select(readonly=True)
        typ, data = self.imap.search(None, 'UNSEEN')
        for num in data[0].split():
            typ, data = self.imap.fetch(num, '(RFC822)')
            raw_mail = data[0][1]
            mail = email.message_from_bytes(raw_mail)
            mail = {
                'Account': account_name,
                'From': email.header.decode_header(mail.get('From')),
                'Subject': email.header.decode_header(mail.get('Subject')),
                'Date': email.header.decode_header(mail.get('Date'))
            }
            mails.append(mail)
        return mails


def mail_check():
    console.log("Starting mail check")
    mails = []
    has_errors = False
    if GlobalSettingsExist() and AccountExist():
        groups = settings.childGroups()
        for i in range(len(groups)):
            settings.beginGroup(groups[i])
            group = groups[i]
            user = settings.value("Login")
            password = settings.value("Password")
            mailserver = settings.value("MailServer")
            port = settings.value("Port")
            ssl = settings.value("SSL")
            settings.endGroup()
            try:
                m = Mail(mailserver, port, ssl, user, password)
                mails.extend(m.checkmail(group))
            except imaplib.IMAP4.error as ex:
                has_errors = True
                console.log(group + ': ' + ex.args[0].decode())
            except (Exception, socket.timeout) as ex:
                has_errors = True
                msg = 'timeout' if type(ex) == socket.timeout else ex.strerror
                console.log('%s: unable to establish connection to mailbox (%s)' % (group, msg))
    else:
        has_errors = True
        console.log("Cannot find configuration file. You should give access to your mailbox")

    # Parsing mail_count values

    if len(mails) == 0:
        # When mailbox have not unread letters
        window.trayIcon.setToolTip("You have no unread mail")
        # Draw text on icon
        pixmap = QtGui.QPixmap(QtGui.QPixmap(":icons/mailbox_error.png" if has_errors else ":icons/mailbox_empty.png"))
        # End drawing text on icon
        window.trayIcon.setIcon(QtGui.QIcon(pixmap))
        console.log("Mail check completed. You have no unread letters")
        details.ui.tableWidget.clearContents()
        details.ui.tableWidget.setRowCount(0)
        details.ui.tableWidget.setColumnCount(0)
    else:
        # When mailbox has unread letters
        window.trayIcon.setToolTip("You have " + str(len(mails)) + " unread letters")
        # Draw text on icon
        pixmap = QtGui.QPixmap(QtGui.QPixmap(":icons/mailbox_error.png" if has_errors else ":icons/mailbox_full.png"))
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setFont(QtGui.QFont('Arial', 100, QtGui.QFont.Bold))
        painter.drawText(QtCore.QRectF(pixmap.rect()), QtCore.Qt.AlignCenter, str(len(mails)))
        painter.end()
        # End drawing text on icon
        window.trayIcon.setIcon(QtGui.QIcon(pixmap))
        # Popup notification appears only if mail count changed since last check
        if len(mails) != window.lastCheckCount:
            notify("You have " + str(len(mails)) + " unread letters")

        # Filling table
        details.ui.tableWidget.setRowCount(len(mails))
        details.ui.tableWidget.setColumnCount(4)
        # Enter data onto Table
        headers = []
        for row, mail in enumerate(mails):
            if not headers:
                headers = sorted(mail.keys())
            for col, key in enumerate(sorted(mail.keys())):
                data = mail[key]
                if type(data) == list:
                    txt = ''
                    for item in data:
                        if type(item[0]) != str:
                            if not item[1] or item[1] == 'unknown-8bit':
                                item = (item[0], 'utf-8')
                            txt += item[0].decode(item[1])
                        else:
                            txt += item[0]
                    data = txt
                newitem = QtWidgets.QTableWidgetItem(data)
                details.ui.tableWidget.setItem(row, col, newitem)
        # Add Header
        details.ui.tableWidget.setHorizontalHeaderLabels(headers)

        # Adjust size of Table
        details.ui.tableWidget.resizeColumnsToContents()
        details.ui.tableWidget.resizeRowsToContents()
        console.log("Mail check completed. You have " + str(len(mails)) + " unread letters")
    # check was successfull, lastCheckCount is updating
    window.lastCheckCount = len(mails)


def notify(message):
    try:
        if settings.value("Notify"):
            subprocess.Popen(['notify-send', programTitle, message])
        return
    except Exception as ex:
        console.log('notify-send: ' + ex.strerror)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    systemtray_timeout = 0
    # Check if DE supports system tray
    while not QSystemTrayIcon.isSystemTrayAvailable():
        systemtray_timeout += 1
        time.sleep(20)
        if systemtray_timeout == 5:
            QMessageBox.critical(None, "Mail notifier",
                                 "I couldn't detect any system tray on this system.")
            sys.exit(1)
    QApplication.setQuitOnLastWindowClosed(False)
    window = Window()
    about = About()
    details = Details()
    console = Console()
    if GlobalSettingsExist() and AccountExist():
        window.hide()
    else:
        window.show()
    # UI started. Starting required functions after UI start
    mail_check()
    window.start()
    sys.exit(app.exec_())
