# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'branchcomparewindow.ui'
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

from qgitc.commitpanel import CommitPanel
from qgitc.emptystatelistview import EmptyStateListView
from qgitc.patchviewer import PatchViewer
from qgitc.searchlineedit import SearchLineEdit
from qgitc.waitingspinnerwidget import QtWaitingSpinner

class Ui_BranchCompareWindow(object):
    def setupUi(self, BranchCompareWindow):
        if not BranchCompareWindow.objectName():
            BranchCompareWindow.setObjectName(u"BranchCompareWindow")
        BranchCompareWindow.resize(851, 633)
        self.centralwidget = QWidget(BranchCompareWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_5 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_3.addWidget(self.label_2)

        self.cbBaseBranch = QComboBox(self.frame_2)
        self.cbBaseBranch.setObjectName(u"cbBaseBranch")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cbBaseBranch.sizePolicy().hasHeightForWidth())
        self.cbBaseBranch.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.cbBaseBranch)

        self.label_3 = QLabel(self.frame_2)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.cbTargetBranch = QComboBox(self.frame_2)
        self.cbTargetBranch.setObjectName(u"cbTargetBranch")
        sizePolicy1.setHeightForWidth(self.cbTargetBranch.sizePolicy().hasHeightForWidth())
        self.cbTargetBranch.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.cbTargetBranch)

        self.btnShowLogWindow = QPushButton(self.frame_2)
        self.btnShowLogWindow.setObjectName(u"btnShowLogWindow")

        self.horizontalLayout_3.addWidget(self.btnShowLogWindow)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.cbMergeBase = QCheckBox(self.frame_2)
        self.cbMergeBase.setObjectName(u"cbMergeBase")
        self.cbMergeBase.setChecked(True)

        self.horizontalLayout_4.addWidget(self.cbMergeBase)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.verticalLayout_5.addWidget(self.frame_2)

        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitterChanges = QSplitter(self.splitter)
        self.splitterChanges.setObjectName(u"splitterChanges")
        self.splitterChanges.setOrientation(Qt.Orientation.Horizontal)
        self.frame = QFrame(self.splitterChanges)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.spinnerFiles = QtWaitingSpinner(self.frame)
        self.spinnerFiles.setObjectName(u"spinnerFiles")

        self.horizontalLayout.addWidget(self.spinnerFiles)

        self.leFileFilter = SearchLineEdit(self.frame)
        self.leFileFilter.setObjectName(u"leFileFilter")

        self.horizontalLayout.addWidget(self.leFileFilter)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.lvFiles = EmptyStateListView(self.frame)
        self.lvFiles.setObjectName(u"lvFiles")

        self.verticalLayout_2.addWidget(self.lvFiles)

        self.splitterChanges.addWidget(self.frame)
        self.verticalLayoutWidget_2 = QWidget(self.splitterChanges)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame_3 = QFrame(self.verticalLayoutWidget_2)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_3)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_4 = QLabel(self.frame_3)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_5.addWidget(self.label_4)

        self.spinnerDiff = QtWaitingSpinner(self.frame_3)
        self.spinnerDiff.setObjectName(u"spinnerDiff")

        self.horizontalLayout_5.addWidget(self.spinnerDiff)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.diffViewer = PatchViewer(self.frame_3)
        self.diffViewer.setObjectName(u"diffViewer")

        self.verticalLayout_4.addWidget(self.diffViewer)


        self.verticalLayout_3.addWidget(self.frame_3)

        self.splitterChanges.addWidget(self.verticalLayoutWidget_2)
        self.splitter.addWidget(self.splitterChanges)
        self.commitPanel = CommitPanel(self.splitter)
        self.commitPanel.setObjectName(u"commitPanel")
        self.commitPanel.setOrientation(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.commitPanel)

        self.verticalLayout_5.addWidget(self.splitter)

        BranchCompareWindow.setCentralWidget(self.centralwidget)
#if QT_CONFIG(shortcut)
        self.label_2.setBuddy(self.cbBaseBranch)
        self.label_3.setBuddy(self.cbTargetBranch)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.leFileFilter, self.lvFiles)

        self.retranslateUi(BranchCompareWindow)

        QMetaObject.connectSlotsByName(BranchCompareWindow)
    # setupUi

    def retranslateUi(self, BranchCompareWindow):
        BranchCompareWindow.setWindowTitle(QCoreApplication.translate("BranchCompareWindow", u"QGitc Branch Compare", None))
        self.label_2.setText(QCoreApplication.translate("BranchCompareWindow", u"&Base Branch:", None))
        self.label_3.setText(QCoreApplication.translate("BranchCompareWindow", u"&Target Branch:", None))
        self.btnShowLogWindow.setText(QCoreApplication.translate("BranchCompareWindow", u"Change &Repository...", None))
#if QT_CONFIG(tooltip)
        self.cbMergeBase.setToolTip(QCoreApplication.translate("BranchCompareWindow", u"Only useful when the target branch has not been merged into the base", None))
#endif // QT_CONFIG(tooltip)
        self.cbMergeBase.setText(QCoreApplication.translate("BranchCompareWindow", u"Use &Merge Base", None))
        self.label_4.setText(QCoreApplication.translate("BranchCompareWindow", u"Diff", None))
    # retranslateUi

