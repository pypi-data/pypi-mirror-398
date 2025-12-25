# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pickbranchwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QVBoxLayout,
    QWidget)

from qgitc.coloredicontoolbutton import ColoredIconToolButton
from qgitc.diffview import DiffView
from qgitc.logview import LogView
from qgitc.waitingspinnerwidget import QtWaitingSpinner

class Ui_PickBranchWindow(object):
    def setupUi(self, PickBranchWindow):
        if not PickBranchWindow.objectName():
            PickBranchWindow.setObjectName(u"PickBranchWindow")
        PickBranchWindow.resize(934, 658)
        self.centralwidget = QWidget(PickBranchWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_main = QVBoxLayout(self.centralwidget)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(4, 4, 4, 4)
        self.frameBranchSelection = QFrame(self.centralwidget)
        self.frameBranchSelection.setObjectName(u"frameBranchSelection")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frameBranchSelection.sizePolicy().hasHeightForWidth())
        self.frameBranchSelection.setSizePolicy(sizePolicy)
        self.frameBranchSelection.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameBranchSelection.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_branches = QVBoxLayout(self.frameBranchSelection)
        self.verticalLayout_branches.setSpacing(3)
        self.verticalLayout_branches.setObjectName(u"verticalLayout_branches")
        self.verticalLayout_branches.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_branches = QHBoxLayout()
        self.horizontalLayout_branches.setObjectName(u"horizontalLayout_branches")
        self.labelSourceBranch = QLabel(self.frameBranchSelection)
        self.labelSourceBranch.setObjectName(u"labelSourceBranch")

        self.horizontalLayout_branches.addWidget(self.labelSourceBranch)

        self.cbSourceBranch = QComboBox(self.frameBranchSelection)
        self.cbSourceBranch.setObjectName(u"cbSourceBranch")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cbSourceBranch.sizePolicy().hasHeightForWidth())
        self.cbSourceBranch.setSizePolicy(sizePolicy1)

        self.horizontalLayout_branches.addWidget(self.cbSourceBranch)

        self.labelBaseBranch = QLabel(self.frameBranchSelection)
        self.labelBaseBranch.setObjectName(u"labelBaseBranch")

        self.horizontalLayout_branches.addWidget(self.labelBaseBranch)

        self.cbBaseBranch = QComboBox(self.frameBranchSelection)
        self.cbBaseBranch.setObjectName(u"cbBaseBranch")
        sizePolicy1.setHeightForWidth(self.cbBaseBranch.sizePolicy().hasHeightForWidth())
        self.cbBaseBranch.setSizePolicy(sizePolicy1)

        self.horizontalLayout_branches.addWidget(self.cbBaseBranch)

        self.btnShowLogWindow = QPushButton(self.frameBranchSelection)
        self.btnShowLogWindow.setObjectName(u"btnShowLogWindow")

        self.horizontalLayout_branches.addWidget(self.btnShowLogWindow)


        self.verticalLayout_branches.addLayout(self.horizontalLayout_branches)

        self.horizontalLayout_cherrypick = QHBoxLayout()
        self.horizontalLayout_cherrypick.setObjectName(u"horizontalLayout_cherrypick")
        self.labelTargetBranch = QLabel(self.frameBranchSelection)
        self.labelTargetBranch.setObjectName(u"labelTargetBranch")

        self.horizontalLayout_cherrypick.addWidget(self.labelTargetBranch)

        self.cbTargetBranch = QComboBox(self.frameBranchSelection)
        self.cbTargetBranch.setObjectName(u"cbTargetBranch")
        sizePolicy1.setHeightForWidth(self.cbTargetBranch.sizePolicy().hasHeightForWidth())
        self.cbTargetBranch.setSizePolicy(sizePolicy1)

        self.horizontalLayout_cherrypick.addWidget(self.cbTargetBranch)

        self.cbRecordOrigin = QCheckBox(self.frameBranchSelection)
        self.cbRecordOrigin.setObjectName(u"cbRecordOrigin")
        self.cbRecordOrigin.setChecked(True)

        self.horizontalLayout_cherrypick.addWidget(self.cbRecordOrigin)

        self.btnCherryPick = QPushButton(self.frameBranchSelection)
        self.btnCherryPick.setObjectName(u"btnCherryPick")
        self.btnCherryPick.setEnabled(False)

        self.horizontalLayout_cherrypick.addWidget(self.btnCherryPick)


        self.verticalLayout_branches.addLayout(self.horizontalLayout_cherrypick)


        self.verticalLayout_main.addWidget(self.frameBranchSelection)

        self.splitterMain = QSplitter(self.centralwidget)
        self.splitterMain.setObjectName(u"splitterMain")
        self.splitterMain.setOrientation(Qt.Orientation.Horizontal)
        self.frameCommits = QFrame(self.splitterMain)
        self.frameCommits.setObjectName(u"frameCommits")
        self.frameCommits.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameCommits.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_commits = QVBoxLayout(self.frameCommits)
        self.verticalLayout_commits.setObjectName(u"verticalLayout_commits")
        self.verticalLayout_commits.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_commits_header = QHBoxLayout()
        self.horizontalLayout_commits_header.setObjectName(u"horizontalLayout_commits_header")
        self.labelCommits = QLabel(self.frameCommits)
        self.labelCommits.setObjectName(u"labelCommits")

        self.horizontalLayout_commits_header.addWidget(self.labelCommits)

        self.spinnerCommits = QtWaitingSpinner(self.frameCommits)
        self.spinnerCommits.setObjectName(u"spinnerCommits")

        self.horizontalLayout_commits_header.addWidget(self.spinnerCommits)

        self.horizontalSpacer_commits = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_commits_header.addItem(self.horizontalSpacer_commits)

        self.btnSelectAll = ColoredIconToolButton(self.frameCommits)
        self.btnSelectAll.setObjectName(u"btnSelectAll")
        self.btnSelectAll.setIconSize(QSize(20, 20))

        self.horizontalLayout_commits_header.addWidget(self.btnSelectAll)

        self.btnSelectNone = ColoredIconToolButton(self.frameCommits)
        self.btnSelectNone.setObjectName(u"btnSelectNone")
        self.btnSelectNone.setIconSize(QSize(20, 20))

        self.horizontalLayout_commits_header.addWidget(self.btnSelectNone)

        self.btnFilterCommits = ColoredIconToolButton(self.frameCommits)
        self.btnFilterCommits.setObjectName(u"btnFilterCommits")
        self.btnFilterCommits.setIconSize(QSize(20, 20))

        self.horizontalLayout_commits_header.addWidget(self.btnFilterCommits)

        self.btnSettings = ColoredIconToolButton(self.frameCommits)
        self.btnSettings.setObjectName(u"btnSettings")
        self.btnSettings.setIconSize(QSize(20, 20))

        self.horizontalLayout_commits_header.addWidget(self.btnSettings)


        self.verticalLayout_commits.addLayout(self.horizontalLayout_commits_header)

        self.logView = LogView(self.frameCommits)
        self.logView.setObjectName(u"logView")

        self.verticalLayout_commits.addWidget(self.logView)

        self.splitterMain.addWidget(self.frameCommits)
        self.splitterRight = QSplitter(self.splitterMain)
        self.splitterRight.setObjectName(u"splitterRight")
        self.splitterRight.setOrientation(Qt.Orientation.Vertical)
        self.diffView = DiffView(self.splitterRight)
        self.diffView.setObjectName(u"diffView")
        self.splitterRight.addWidget(self.diffView)
        self.splitterMain.addWidget(self.splitterRight)

        self.verticalLayout_main.addWidget(self.splitterMain)

        self.frameActions = QFrame(self.centralwidget)
        self.frameActions.setObjectName(u"frameActions")
        sizePolicy.setHeightForWidth(self.frameActions.sizePolicy().hasHeightForWidth())
        self.frameActions.setSizePolicy(sizePolicy)
        self.frameActions.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameActions.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_actions = QHBoxLayout(self.frameActions)
        self.horizontalLayout_actions.setObjectName(u"horizontalLayout_actions")
        self.horizontalLayout_actions.setContentsMargins(4, 4, 4, 4)
        self.labelStatus = QLabel(self.frameActions)
        self.labelStatus.setObjectName(u"labelStatus")

        self.horizontalLayout_actions.addWidget(self.labelStatus)


        self.verticalLayout_main.addWidget(self.frameActions)

        PickBranchWindow.setCentralWidget(self.centralwidget)
#if QT_CONFIG(shortcut)
        self.labelSourceBranch.setBuddy(self.cbSourceBranch)
        self.labelBaseBranch.setBuddy(self.cbBaseBranch)
        self.labelTargetBranch.setBuddy(self.cbTargetBranch)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.cbSourceBranch, self.cbBaseBranch)
        QWidget.setTabOrder(self.cbBaseBranch, self.btnShowLogWindow)
        QWidget.setTabOrder(self.btnShowLogWindow, self.cbTargetBranch)
        QWidget.setTabOrder(self.cbTargetBranch, self.cbRecordOrigin)
        QWidget.setTabOrder(self.cbRecordOrigin, self.btnCherryPick)
        QWidget.setTabOrder(self.btnCherryPick, self.btnSelectAll)
        QWidget.setTabOrder(self.btnSelectAll, self.btnSelectNone)

        self.retranslateUi(PickBranchWindow)

        QMetaObject.connectSlotsByName(PickBranchWindow)
    # setupUi

    def retranslateUi(self, PickBranchWindow):
        PickBranchWindow.setWindowTitle(QCoreApplication.translate("PickBranchWindow", u"QGitc Cherry Pick", None))
        self.labelSourceBranch.setText(QCoreApplication.translate("PickBranchWindow", u"&Source Branch:", None))
#if QT_CONFIG(tooltip)
        self.cbSourceBranch.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Select the source branch to cherry-pick commits from", None))
#endif // QT_CONFIG(tooltip)
        self.labelBaseBranch.setText(QCoreApplication.translate("PickBranchWindow", u"&Base Branch:", None))
#if QT_CONFIG(tooltip)
        self.cbBaseBranch.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Select the base branch to exclude its commits (shows commits in source but not in base)", None))
#endif // QT_CONFIG(tooltip)
        self.btnShowLogWindow.setText(QCoreApplication.translate("PickBranchWindow", u"Change &Repository...", None))
        self.labelTargetBranch.setText(QCoreApplication.translate("PickBranchWindow", u"&Target Branch:", None))
#if QT_CONFIG(tooltip)
        self.cbTargetBranch.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Select the target branch to cherry-pick commits to", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.cbRecordOrigin.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Record the origin commit SHA in the cherry-picked commit message (-x option)", None))
#endif // QT_CONFIG(tooltip)
        self.cbRecordOrigin.setText(QCoreApplication.translate("PickBranchWindow", u"&Record Origin", None))
#if QT_CONFIG(tooltip)
        self.btnCherryPick.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Cherry-pick selected commits to target branch", None))
#endif // QT_CONFIG(tooltip)
        self.btnCherryPick.setText(QCoreApplication.translate("PickBranchWindow", u"Cherry-&Pick", None))
        self.labelCommits.setText(QCoreApplication.translate("PickBranchWindow", u"Commits to Cherry-Pick", None))
#if QT_CONFIG(tooltip)
        self.btnSelectAll.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Select all commits", None))
#endif // QT_CONFIG(tooltip)
        self.btnSelectAll.setText("")
#if QT_CONFIG(tooltip)
        self.btnSelectNone.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Deselect all commits", None))
#endif // QT_CONFIG(tooltip)
        self.btnSelectNone.setText("")
#if QT_CONFIG(tooltip)
        self.btnFilterCommits.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Filter commits based on Commit Filters settings", None))
#endif // QT_CONFIG(tooltip)
        self.btnFilterCommits.setText("")
#if QT_CONFIG(tooltip)
        self.btnSettings.setToolTip(QCoreApplication.translate("PickBranchWindow", u"Open cherry-pick settings", None))
#endif // QT_CONFIG(tooltip)
        self.btnSettings.setText("")
        self.labelStatus.setText(QCoreApplication.translate("PickBranchWindow", u"Ready", None))
    # retranslateUi

