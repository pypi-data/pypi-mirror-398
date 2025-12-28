# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(647, 525)
        MainWindow.setMinimumSize(QSize(647, 525))
        MainWindow.setMaximumSize(QSize(647, 525))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 647, 525))
        self.tabWidget.setMinimumSize(QSize(647, 525))
        self.tabWidget.setMaximumSize(QSize(647, 525))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.layoutWidget = QWidget(self.tab)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 10, 481, 26))
        self.horizontalLayout_3 = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.layoutWidget)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_3.addWidget(self.label_7)

        self.saleReportPath_LE = QLineEdit(self.layoutWidget)
        self.saleReportPath_LE.setObjectName(u"saleReportPath_LE")

        self.horizontalLayout_3.addWidget(self.saleReportPath_LE)

        self.selectSaleFolder_PB = QPushButton(self.layoutWidget)
        self.selectSaleFolder_PB.setObjectName(u"selectSaleFolder_PB")

        self.horizontalLayout_3.addWidget(self.selectSaleFolder_PB)

        self.layoutWidget1 = QWidget(self.tab)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(500, 10, 131, 116))
        self.verticalLayout = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.weeklyReport_PB = QPushButton(self.layoutWidget1)
        self.weeklyReport_PB.setObjectName(u"weeklyReport_PB")

        self.verticalLayout.addWidget(self.weeklyReport_PB)

        self.processReport_PB = QPushButton(self.layoutWidget1)
        self.processReport_PB.setObjectName(u"processReport_PB")

        self.verticalLayout.addWidget(self.processReport_PB)

        self.consolidation_PB = QPushButton(self.layoutWidget1)
        self.consolidation_PB.setObjectName(u"consolidation_PB")

        self.verticalLayout.addWidget(self.consolidation_PB)

        self.close_PB = QPushButton(self.layoutWidget1)
        self.close_PB.setObjectName(u"close_PB")

        self.verticalLayout.addWidget(self.close_PB)

        self.layoutWidget2 = QWidget(self.tab)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(10, 40, 481, 31))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_12 = QLabel(self.layoutWidget2)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout.addWidget(self.label_12)

        self.stockReportPath_LE = QLineEdit(self.layoutWidget2)
        self.stockReportPath_LE.setObjectName(u"stockReportPath_LE")

        self.horizontalLayout.addWidget(self.stockReportPath_LE)

        self.selectStockFolder_PB = QPushButton(self.layoutWidget2)
        self.selectStockFolder_PB.setObjectName(u"selectStockFolder_PB")

        self.horizontalLayout.addWidget(self.selectStockFolder_PB)

        self.layoutWidget_5 = QWidget(self.tab)
        self.layoutWidget_5.setObjectName(u"layoutWidget_5")
        self.layoutWidget_5.setGeometry(QRect(10, 70, 481, 26))
        self.horizontalLayout_7 = QHBoxLayout(self.layoutWidget_5)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_13 = QLabel(self.layoutWidget_5)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_7.addWidget(self.label_13)

        self.masterFilePath_LE = QLineEdit(self.layoutWidget_5)
        self.masterFilePath_LE.setObjectName(u"masterFilePath_LE")

        self.horizontalLayout_7.addWidget(self.masterFilePath_LE)

        self.selectMasterFolder_PB = QPushButton(self.layoutWidget_5)
        self.selectMasterFolder_PB.setObjectName(u"selectMasterFolder_PB")

        self.horizontalLayout_7.addWidget(self.selectMasterFolder_PB)

        self.layoutWidget_6 = QWidget(self.tab)
        self.layoutWidget_6.setObjectName(u"layoutWidget_6")
        self.layoutWidget_6.setGeometry(QRect(10, 100, 481, 26))
        self.horizontalLayout_8 = QHBoxLayout(self.layoutWidget_6)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_14 = QLabel(self.layoutWidget_6)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_8.addWidget(self.label_14)

        self.dataFilesPath_LE = QLineEdit(self.layoutWidget_6)
        self.dataFilesPath_LE.setObjectName(u"dataFilesPath_LE")

        self.horizontalLayout_8.addWidget(self.dataFilesPath_LE)

        self.selectDataFolder_PB = QPushButton(self.layoutWidget_6)
        self.selectDataFolder_PB.setObjectName(u"selectDataFolder_PB")

        self.horizontalLayout_8.addWidget(self.selectDataFolder_PB)

        self.layoutWidget3 = QWidget(self.tab)
        self.layoutWidget3.setObjectName(u"layoutWidget3")
        self.layoutWidget3.setGeometry(QRect(492, 140, 146, 92))
        self.verticalLayout_2 = QVBoxLayout(self.layoutWidget3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_17 = QLabel(self.layoutWidget3)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_9.addWidget(self.label_17)

        self.selectSeason_CB = QComboBox(self.layoutWidget3)
        self.selectSeason_CB.setObjectName(u"selectSeason_CB")

        self.horizontalLayout_9.addWidget(self.selectSeason_CB)


        self.verticalLayout_2.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_10 = QLabel(self.layoutWidget3)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_5.addWidget(self.label_10)

        self.selectWeek_CB = QComboBox(self.layoutWidget3)
        self.selectWeek_CB.setObjectName(u"selectWeek_CB")

        self.horizontalLayout_5.addWidget(self.selectWeek_CB)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_11 = QLabel(self.layoutWidget3)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_6.addWidget(self.label_11)

        self.selectBrand_CB = QComboBox(self.layoutWidget3)
        self.selectBrand_CB.setObjectName(u"selectBrand_CB")

        self.horizontalLayout_6.addWidget(self.selectBrand_CB)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.layoutWidget4 = QWidget(self.tab)
        self.layoutWidget4.setObjectName(u"layoutWidget4")
        self.layoutWidget4.setGeometry(QRect(10, 280, 621, 26))
        self.horizontalLayout_10 = QHBoxLayout(self.layoutWidget4)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_18 = QLabel(self.layoutWidget4)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_10.addWidget(self.label_18)

        self.imgFolderPath_LE = QLineEdit(self.layoutWidget4)
        self.imgFolderPath_LE.setObjectName(u"imgFolderPath_LE")

        self.horizontalLayout_10.addWidget(self.imgFolderPath_LE)

        self.imgSelect_PB = QPushButton(self.layoutWidget4)
        self.imgSelect_PB.setObjectName(u"imgSelect_PB")

        self.horizontalLayout_10.addWidget(self.imgSelect_PB)

        self.insertImg_PB = QPushButton(self.layoutWidget4)
        self.insertImg_PB.setObjectName(u"insertImg_PB")

        self.horizontalLayout_10.addWidget(self.insertImg_PB)

        self.okSaleItem_cBox = QCheckBox(self.tab)
        self.okSaleItem_cBox.setObjectName(u"okSaleItem_cBox")
        self.okSaleItem_cBox.setGeometry(QRect(10, 320, 114, 22))
        self.outpout_TE = QTextEdit(self.tab)
        self.outpout_TE.setObjectName(u"outpout_TE")
        self.outpout_TE.setGeometry(QRect(10, 430, 621, 51))
        self.outpout_TE.setFrameShape(QFrame.Shape.Box)
        self.layoutWidget5 = QWidget(self.tab)
        self.layoutWidget5.setObjectName(u"layoutWidget5")
        self.layoutWidget5.setGeometry(QRect(10, 140, 471, 128))
        self.verticalLayout_13 = QVBoxLayout(self.layoutWidget5)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(self.layoutWidget5)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)

        self.ytdStart_DE = QDateEdit(self.layoutWidget5)
        self.ytdStart_DE.setObjectName(u"ytdStart_DE")
        self.ytdStart_DE.setDateTime(QDateTime(QDate(2023, 12, 27), QTime(0, 0, 0)))

        self.horizontalLayout_2.addWidget(self.ytdStart_DE)

        self.label_4 = QLabel(self.layoutWidget5)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_2.addWidget(self.label_4)

        self.ytdEnd_DE = QDateEdit(self.layoutWidget5)
        self.ytdEnd_DE.setObjectName(u"ytdEnd_DE")
        self.ytdEnd_DE.setDateTime(QDateTime(QDate(2024, 7, 27), QTime(0, 0, 0)))

        self.horizontalLayout_2.addWidget(self.ytdEnd_DE)


        self.verticalLayout_13.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_2 = QLabel(self.layoutWidget5)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)

        self.mtdStart_DE = QDateEdit(self.layoutWidget5)
        self.mtdStart_DE.setObjectName(u"mtdStart_DE")
        self.mtdStart_DE.setDateTime(QDateTime(QDate(2024, 7, 27), QTime(0, 0, 0)))

        self.horizontalLayout_4.addWidget(self.mtdStart_DE)

        self.label_5 = QLabel(self.layoutWidget5)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_4.addWidget(self.label_5)

        self.mtdEnd_DE = QDateEdit(self.layoutWidget5)
        self.mtdEnd_DE.setObjectName(u"mtdEnd_DE")
        self.mtdEnd_DE.setDateTime(QDateTime(QDate(2024, 8, 26), QTime(0, 0, 0)))

        self.horizontalLayout_4.addWidget(self.mtdEnd_DE)


        self.verticalLayout_13.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_3 = QLabel(self.layoutWidget5)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_11.addWidget(self.label_3)

        self.wtdStart_DE = QDateEdit(self.layoutWidget5)
        self.wtdStart_DE.setObjectName(u"wtdStart_DE")
        self.wtdStart_DE.setDateTime(QDateTime(QDate(2024, 7, 31), QTime(0, 0, 0)))

        self.horizontalLayout_11.addWidget(self.wtdStart_DE)

        self.label_6 = QLabel(self.layoutWidget5)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_11.addWidget(self.label_6)

        self.wtdEnd_DE = QDateEdit(self.layoutWidget5)
        self.wtdEnd_DE.setObjectName(u"wtdEnd_DE")
        self.wtdEnd_DE.setDateTime(QDateTime(QDate(2024, 8, 7), QTime(0, 0, 0)))

        self.horizontalLayout_11.addWidget(self.wtdEnd_DE)


        self.verticalLayout_13.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_16 = QLabel(self.layoutWidget5)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_12.addWidget(self.label_16)

        self.lywtdStart_DE = QDateEdit(self.layoutWidget5)
        self.lywtdStart_DE.setObjectName(u"lywtdStart_DE")
        self.lywtdStart_DE.setDateTime(QDateTime(QDate(2024, 7, 30), QTime(20, 0, 0)))

        self.horizontalLayout_12.addWidget(self.lywtdStart_DE)

        self.label_15 = QLabel(self.layoutWidget5)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_12.addWidget(self.label_15)

        self.lywtdEnd_DE = QDateEdit(self.layoutWidget5)
        self.lywtdEnd_DE.setObjectName(u"lywtdEnd_DE")
        self.lywtdEnd_DE.setDateTime(QDateTime(QDate(2024, 8, 6), QTime(20, 0, 0)))

        self.horizontalLayout_12.addWidget(self.lywtdEnd_DE)


        self.verticalLayout_13.addLayout(self.horizontalLayout_12)

        self.layoutWidget6 = QWidget(self.tab)
        self.layoutWidget6.setObjectName(u"layoutWidget6")
        self.layoutWidget6.setGeometry(QRect(10, 350, 621, 71))
        self.verticalLayout_14 = QVBoxLayout(self.layoutWidget6)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.jcST_PB = QPushButton(self.layoutWidget6)
        self.jcST_PB.setObjectName(u"jcST_PB")

        self.horizontalLayout_13.addWidget(self.jcST_PB)

        self.okST_PB = QPushButton(self.layoutWidget6)
        self.okST_PB.setObjectName(u"okST_PB")

        self.horizontalLayout_13.addWidget(self.okST_PB)

        self.paNST_PB = QPushButton(self.layoutWidget6)
        self.paNST_PB.setObjectName(u"paNST_PB")

        self.horizontalLayout_13.addWidget(self.paNST_PB)

        self.uzST_PB = QPushButton(self.layoutWidget6)
        self.uzST_PB.setObjectName(u"uzST_PB")

        self.horizontalLayout_13.addWidget(self.uzST_PB)

        self.viST_PB = QPushButton(self.layoutWidget6)
        self.viST_PB.setObjectName(u"viST_PB")

        self.horizontalLayout_13.addWidget(self.viST_PB)


        self.verticalLayout_14.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.okSR_PB = QPushButton(self.layoutWidget6)
        self.okSR_PB.setObjectName(u"okSR_PB")

        self.horizontalLayout_14.addWidget(self.okSR_PB)

        self.okBS_PB = QPushButton(self.layoutWidget6)
        self.okBS_PB.setObjectName(u"okBS_PB")

        self.horizontalLayout_14.addWidget(self.okBS_PB)

        self.paNStk_PB = QPushButton(self.layoutWidget6)
        self.paNStk_PB.setObjectName(u"paNStk_PB")

        self.horizontalLayout_14.addWidget(self.paNStk_PB)

        self.uzBS_PB = QPushButton(self.layoutWidget6)
        self.uzBS_PB.setObjectName(u"uzBS_PB")

        self.horizontalLayout_14.addWidget(self.uzBS_PB)

        self.viBS_PB = QPushButton(self.layoutWidget6)
        self.viBS_PB.setObjectName(u"viBS_PB")

        self.horizontalLayout_14.addWidget(self.viBS_PB)


        self.verticalLayout_14.addLayout(self.horizontalLayout_14)

        self.tabWidget.addTab(self.tab, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.layoutWidget_2 = QWidget(self.tab_3)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(400, 90, 71, 71))
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_8 = QLabel(self.layoutWidget_2)
        self.label_8.setObjectName(u"label_8")

        self.verticalLayout_3.addWidget(self.label_8)

        self.label_9 = QLabel(self.layoutWidget_2)
        self.label_9.setObjectName(u"label_9")

        self.verticalLayout_3.addWidget(self.label_9)

        self.layoutWidget_3 = QWidget(self.tab_3)
        self.layoutWidget_3.setObjectName(u"layoutWidget_3")
        self.layoutWidget_3.setGeometry(QRect(90, 90, 151, 71))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.stkStartDE = QDateEdit(self.layoutWidget_3)
        self.stkStartDE.setObjectName(u"stkStartDE")

        self.verticalLayout_4.addWidget(self.stkStartDE)

        self.slsStartDE = QDateEdit(self.layoutWidget_3)
        self.slsStartDE.setObjectName(u"slsStartDE")

        self.verticalLayout_4.addWidget(self.slsStartDE)

        self.layoutWidget_4 = QWidget(self.tab_3)
        self.layoutWidget_4.setObjectName(u"layoutWidget_4")
        self.layoutWidget_4.setGeometry(QRect(10, 90, 71, 71))
        self.verticalLayout_5 = QVBoxLayout(self.layoutWidget_4)
        self.verticalLayout_5.setSpacing(2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_19 = QLabel(self.layoutWidget_4)
        self.label_19.setObjectName(u"label_19")

        self.verticalLayout_5.addWidget(self.label_19)

        self.label_20 = QLabel(self.layoutWidget_4)
        self.label_20.setObjectName(u"label_20")

        self.verticalLayout_5.addWidget(self.label_20)

        self.label_21 = QLabel(self.tab_3)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setGeometry(QRect(10, 20, 301, 21))
        self.layoutWidget_7 = QWidget(self.tab_3)
        self.layoutWidget_7.setObjectName(u"layoutWidget_7")
        self.layoutWidget_7.setGeometry(QRect(10, 220, 621, 23))
        self.horizontalLayout_15 = QHBoxLayout(self.layoutWidget_7)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.jcCB = QCheckBox(self.layoutWidget_7)
        self.jcCB.setObjectName(u"jcCB")

        self.horizontalLayout_15.addWidget(self.jcCB)

        self.okCB = QCheckBox(self.layoutWidget_7)
        self.okCB.setObjectName(u"okCB")

        self.horizontalLayout_15.addWidget(self.okCB)

        self.paCB = QCheckBox(self.layoutWidget_7)
        self.paCB.setObjectName(u"paCB")

        self.horizontalLayout_15.addWidget(self.paCB)

        self.uzCB = QCheckBox(self.layoutWidget_7)
        self.uzCB.setObjectName(u"uzCB")

        self.horizontalLayout_15.addWidget(self.uzCB)

        self.viCB = QCheckBox(self.layoutWidget_7)
        self.viCB.setObjectName(u"viCB")

        self.horizontalLayout_15.addWidget(self.viCB)

        self.yrCB = QCheckBox(self.layoutWidget_7)
        self.yrCB.setObjectName(u"yrCB")

        self.horizontalLayout_15.addWidget(self.yrCB)

        self.lsCB = QCheckBox(self.layoutWidget_7)
        self.lsCB.setObjectName(u"lsCB")

        self.horizontalLayout_15.addWidget(self.lsCB)

        self.layoutWidget_9 = QWidget(self.tab_3)
        self.layoutWidget_9.setObjectName(u"layoutWidget_9")
        self.layoutWidget_9.setGeometry(QRect(480, 90, 151, 71))
        self.verticalLayout_7 = QVBoxLayout(self.layoutWidget_9)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.stkEndDE = QDateEdit(self.layoutWidget_9)
        self.stkEndDE.setObjectName(u"stkEndDE")

        self.verticalLayout_7.addWidget(self.stkEndDE)

        self.slsEndDE = QDateEdit(self.layoutWidget_9)
        self.slsEndDE.setObjectName(u"slsEndDE")

        self.verticalLayout_7.addWidget(self.slsEndDE)

        self.layoutWidget7 = QWidget(self.tab_3)
        self.layoutWidget7.setObjectName(u"layoutWidget7")
        self.layoutWidget7.setGeometry(QRect(10, 260, 621, 26))
        self.horizontalLayout_16 = QHBoxLayout(self.layoutWidget7)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.stockPB = QPushButton(self.layoutWidget7)
        self.stockPB.setObjectName(u"stockPB")

        self.horizontalLayout_16.addWidget(self.stockPB)

        self.salePB = QPushButton(self.layoutWidget7)
        self.salePB.setObjectName(u"salePB")

        self.horizontalLayout_16.addWidget(self.salePB)

        self.purchasePB = QPushButton(self.layoutWidget7)
        self.purchasePB.setObjectName(u"purchasePB")

        self.horizontalLayout_16.addWidget(self.purchasePB)

        self.saleofferPB = QPushButton(self.layoutWidget7)
        self.saleofferPB.setObjectName(u"saleofferPB")

        self.horizontalLayout_16.addWidget(self.saleofferPB)

        self.itempricePB = QPushButton(self.layoutWidget7)
        self.itempricePB.setObjectName(u"itempricePB")

        self.horizontalLayout_16.addWidget(self.itempricePB)

        self.firstpurchPB = QPushButton(self.layoutWidget7)
        self.firstpurchPB.setObjectName(u"firstpurchPB")

        self.horizontalLayout_16.addWidget(self.firstpurchPB)

        self.layoutWidget8 = QWidget(self.tab_3)
        self.layoutWidget8.setObjectName(u"layoutWidget8")
        self.layoutWidget8.setGeometry(QRect(300, 300, 331, 26))
        self.horizontalLayout_17 = QHBoxLayout(self.layoutWidget8)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.transferPB = QPushButton(self.layoutWidget8)
        self.transferPB.setObjectName(u"transferPB")

        self.horizontalLayout_17.addWidget(self.transferPB)

        self.OfferItemPB = QPushButton(self.layoutWidget8)
        self.OfferItemPB.setObjectName(u"OfferItemPB")

        self.horizontalLayout_17.addWidget(self.OfferItemPB)

        self.Rename_PB = QPushButton(self.layoutWidget8)
        self.Rename_PB.setObjectName(u"Rename_PB")

        self.horizontalLayout_17.addWidget(self.Rename_PB)

        self.layoutWidget9 = QWidget(self.tab_3)
        self.layoutWidget9.setObjectName(u"layoutWidget9")
        self.layoutWidget9.setGeometry(QRect(10, 50, 621, 26))
        self.horizontalLayout_18 = QHBoxLayout(self.layoutWidget9)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.dumpFolder_LE = QLineEdit(self.layoutWidget9)
        self.dumpFolder_LE.setObjectName(u"dumpFolder_LE")

        self.horizontalLayout_18.addWidget(self.dumpFolder_LE)

        self.SelectFolder_PB = QPushButton(self.layoutWidget9)
        self.SelectFolder_PB.setObjectName(u"SelectFolder_PB")

        self.horizontalLayout_18.addWidget(self.SelectFolder_PB)

        self.label_25 = QLabel(self.tab_3)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setGeometry(QRect(10, 341, 491, 21))
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.layoutWidget10 = QWidget(self.tab_2)
        self.layoutWidget10.setObjectName(u"layoutWidget10")
        self.layoutWidget10.setGeometry(QRect(90, 30, 531, 116))
        self.verticalLayout_16 = QVBoxLayout(self.layoutWidget10)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.leURL = QLineEdit(self.layoutWidget10)
        self.leURL.setObjectName(u"leURL")

        self.verticalLayout_16.addWidget(self.leURL)

        self.leUserID = QLineEdit(self.layoutWidget10)
        self.leUserID.setObjectName(u"leUserID")

        self.verticalLayout_16.addWidget(self.leUserID)

        self.lePassword = QLineEdit(self.layoutWidget10)
        self.lePassword.setObjectName(u"lePassword")

        self.verticalLayout_16.addWidget(self.lePassword)

        self.leToken = QLineEdit(self.layoutWidget10)
        self.leToken.setObjectName(u"leToken")

        self.verticalLayout_16.addWidget(self.leToken)

        self.layoutWidget11 = QWidget(self.tab_2)
        self.layoutWidget11.setObjectName(u"layoutWidget11")
        self.layoutWidget11.setGeometry(QRect(10, 30, 71, 121))
        self.verticalLayout_17 = QVBoxLayout(self.layoutWidget11)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.lblURL = QLabel(self.layoutWidget11)
        self.lblURL.setObjectName(u"lblURL")

        self.verticalLayout_17.addWidget(self.lblURL)

        self.lblUserID = QLabel(self.layoutWidget11)
        self.lblUserID.setObjectName(u"lblUserID")

        self.verticalLayout_17.addWidget(self.lblUserID)

        self.lblPassword = QLabel(self.layoutWidget11)
        self.lblPassword.setObjectName(u"lblPassword")

        self.verticalLayout_17.addWidget(self.lblPassword)

        self.lblToken = QLabel(self.layoutWidget11)
        self.lblToken.setObjectName(u"lblToken")

        self.verticalLayout_17.addWidget(self.lblToken)

        self.layoutWidget12 = QWidget(self.tab_2)
        self.layoutWidget12.setObjectName(u"layoutWidget12")
        self.layoutWidget12.setGeometry(QRect(90, 230, 371, 26))
        self.horizontalLayout_19 = QHBoxLayout(self.layoutWidget12)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.pbCRMToken = QPushButton(self.layoutWidget12)
        self.pbCRMToken.setObjectName(u"pbCRMToken")

        self.horizontalLayout_19.addWidget(self.pbCRMToken)

        self.pbDownloadReport = QPushButton(self.layoutWidget12)
        self.pbDownloadReport.setObjectName(u"pbDownloadReport")

        self.horizontalLayout_19.addWidget(self.pbDownloadReport)

        self.pbCRMWebSC = QPushButton(self.layoutWidget12)
        self.pbCRMWebSC.setObjectName(u"pbCRMWebSC")

        self.horizontalLayout_19.addWidget(self.pbCRMWebSC)

        self.layoutWidget13 = QWidget(self.tab_2)
        self.layoutWidget13.setObjectName(u"layoutWidget13")
        self.layoutWidget13.setGeometry(QRect(90, 170, 291, 27))
        self.horizontalLayout_20 = QHBoxLayout(self.layoutWidget13)
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_20.setContentsMargins(0, 0, 0, 0)
        self.dateEdit = QDateEdit(self.layoutWidget13)
        self.dateEdit.setObjectName(u"dateEdit")

        self.horizontalLayout_20.addWidget(self.dateEdit)

        self.dateEdit_2 = QDateEdit(self.layoutWidget13)
        self.dateEdit_2.setObjectName(u"dateEdit_2")

        self.horizontalLayout_20.addWidget(self.dateEdit_2)

        self.label_24 = QLabel(self.tab_2)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setGeometry(QRect(10, 320, 611, 21))
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.line = QFrame(self.tab_4)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(10, 100, 601, 20))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.line_2 = QFrame(self.tab_4)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setGeometry(QRect(10, 210, 601, 20))
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)
        self.layoutWidget14 = QWidget(self.tab_4)
        self.layoutWidget14.setObjectName(u"layoutWidget14")
        self.layoutWidget14.setGeometry(QRect(11, 10, 71, 71))
        self.verticalLayout_9 = QVBoxLayout(self.layoutWidget14)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_22 = QLabel(self.layoutWidget14)
        self.label_22.setObjectName(u"label_22")

        self.verticalLayout_9.addWidget(self.label_22)

        self.label_23 = QLabel(self.layoutWidget14)
        self.label_23.setObjectName(u"label_23")

        self.verticalLayout_9.addWidget(self.label_23)

        self.layoutWidget15 = QWidget(self.tab_4)
        self.layoutWidget15.setObjectName(u"layoutWidget15")
        self.layoutWidget15.setGeometry(QRect(88, -1, 431, 91))
        self.verticalLayout_8 = QVBoxLayout(self.layoutWidget15)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.lineEdit = QLineEdit(self.layoutWidget15)
        self.lineEdit.setObjectName(u"lineEdit")

        self.verticalLayout_8.addWidget(self.lineEdit)

        self.lineEdit_2 = QLineEdit(self.layoutWidget15)
        self.lineEdit_2.setObjectName(u"lineEdit_2")

        self.verticalLayout_8.addWidget(self.lineEdit_2)

        self.layoutWidget16 = QWidget(self.tab_4)
        self.layoutWidget16.setObjectName(u"layoutWidget16")
        self.layoutWidget16.setGeometry(QRect(531, 10, 91, 101))
        self.verticalLayout_6 = QVBoxLayout(self.layoutWidget16)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.layoutWidget16)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout_6.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.layoutWidget16)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.verticalLayout_6.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.layoutWidget16)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.verticalLayout_6.addWidget(self.pushButton_3)

        self.layoutWidget17 = QWidget(self.tab_4)
        self.layoutWidget17.setObjectName(u"layoutWidget17")
        self.layoutWidget17.setGeometry(QRect(10, 120, 82, 56))
        self.verticalLayout_10 = QVBoxLayout(self.layoutWidget17)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.pushButton_6 = QPushButton(self.layoutWidget17)
        self.pushButton_6.setObjectName(u"pushButton_6")

        self.verticalLayout_10.addWidget(self.pushButton_6)

        self.pushButton_12 = QPushButton(self.layoutWidget17)
        self.pushButton_12.setObjectName(u"pushButton_12")

        self.verticalLayout_10.addWidget(self.pushButton_12)

        self.layoutWidget18 = QWidget(self.tab_4)
        self.layoutWidget18.setObjectName(u"layoutWidget18")
        self.layoutWidget18.setGeometry(QRect(110, 120, 91, 56))
        self.verticalLayout_11 = QVBoxLayout(self.layoutWidget18)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.pushButton_7 = QPushButton(self.layoutWidget18)
        self.pushButton_7.setObjectName(u"pushButton_7")

        self.verticalLayout_11.addWidget(self.pushButton_7)

        self.pushButton_8 = QPushButton(self.layoutWidget18)
        self.pushButton_8.setObjectName(u"pushButton_8")

        self.verticalLayout_11.addWidget(self.pushButton_8)

        self.layoutWidget19 = QWidget(self.tab_4)
        self.layoutWidget19.setObjectName(u"layoutWidget19")
        self.layoutWidget19.setGeometry(QRect(220, 120, 91, 56))
        self.verticalLayout_12 = QVBoxLayout(self.layoutWidget19)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.pushButton_9 = QPushButton(self.layoutWidget19)
        self.pushButton_9.setObjectName(u"pushButton_9")

        self.verticalLayout_12.addWidget(self.pushButton_9)

        self.pushButton_10 = QPushButton(self.layoutWidget19)
        self.pushButton_10.setObjectName(u"pushButton_10")

        self.verticalLayout_12.addWidget(self.pushButton_10)

        self.layoutWidget20 = QWidget(self.tab_4)
        self.layoutWidget20.setObjectName(u"layoutWidget20")
        self.layoutWidget20.setGeometry(QRect(330, 120, 111, 56))
        self.verticalLayout_15 = QVBoxLayout(self.layoutWidget20)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.pushButton_11 = QPushButton(self.layoutWidget20)
        self.pushButton_11.setObjectName(u"pushButton_11")

        self.verticalLayout_15.addWidget(self.pushButton_11)

        self.pushButton_4 = QPushButton(self.layoutWidget20)
        self.pushButton_4.setObjectName(u"pushButton_4")

        self.verticalLayout_15.addWidget(self.pushButton_4)

        self.dateEdit_3 = QDateEdit(self.tab_4)
        self.dateEdit_3.setObjectName(u"dateEdit_3")
        self.dateEdit_3.setGeometry(QRect(10, 190, 110, 22))
        self.dateEdit_4 = QDateEdit(self.tab_4)
        self.dateEdit_4.setObjectName(u"dateEdit_4")
        self.dateEdit_4.setGeometry(QRect(130, 190, 110, 22))
        self.comboBox = QComboBox(self.tab_4)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(270, 190, 55, 22))
        self.label_26 = QLabel(self.tab_4)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setGeometry(QRect(10, 230, 491, 16))
        self.layoutWidget21 = QWidget(self.tab_4)
        self.layoutWidget21.setObjectName(u"layoutWidget21")
        self.layoutWidget21.setGeometry(QRect(460, 120, 111, 51))
        self.verticalLayout_18 = QVBoxLayout(self.layoutWidget21)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.pushButton_5 = QPushButton(self.layoutWidget21)
        self.pushButton_5.setObjectName(u"pushButton_5")

        self.verticalLayout_18.addWidget(self.pushButton_5)

        self.pushButton_13 = QPushButton(self.layoutWidget21)
        self.pushButton_13.setObjectName(u"pushButton_13")

        self.verticalLayout_18.addWidget(self.pushButton_13)

        self.tabWidget.addTab(self.tab_4, "")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Sale File Path    ", None))
        self.selectSaleFolder_PB.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.weeklyReport_PB.setText(QCoreApplication.translate("MainWindow", u"Weekly Report", None))
        self.processReport_PB.setText(QCoreApplication.translate("MainWindow", u"Combined Report", None))
        self.consolidation_PB.setText(QCoreApplication.translate("MainWindow", u"Consolidation Report", None))
        self.close_PB.setText(QCoreApplication.translate("MainWindow", u"Close and Exit", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Stock File Path  ", None))
        self.selectStockFolder_PB.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Master File Path", None))
        self.selectMasterFolder_PB.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Data File Path    ", None))
        self.selectDataFolder_PB.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Select Season", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Select Week", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Select Brand", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Image Folder Path", None))
        self.imgSelect_PB.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.insertImg_PB.setText(QCoreApplication.translate("MainWindow", u"Insert Image", None))
        self.okSaleItem_cBox.setText(QCoreApplication.translate("MainWindow", u"Exclude SaleItem", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"YTD Start", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"YTD End", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"MTD Start", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"MTD End", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"WTD Start", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"WTD End", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"LY WTD Start", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"LY WTD End", None))
        self.jcST_PB.setText(QCoreApplication.translate("MainWindow", u"JC SellThru", None))
        self.okST_PB.setText(QCoreApplication.translate("MainWindow", u"OK SellThru", None))
        self.paNST_PB.setText(QCoreApplication.translate("MainWindow", u"PA SellThru", None))
        self.uzST_PB.setText(QCoreApplication.translate("MainWindow", u"UZ SellThru", None))
        self.viST_PB.setText(QCoreApplication.translate("MainWindow", u"Vincci SellThru", None))
        self.okSR_PB.setText(QCoreApplication.translate("MainWindow", u"OK Stock Report", None))
        self.okBS_PB.setText(QCoreApplication.translate("MainWindow", u"OK BestSeller", None))
        self.paNStk_PB.setText(QCoreApplication.translate("MainWindow", u"PA BestSeller", None))
        self.uzBS_PB.setText(QCoreApplication.translate("MainWindow", u"UZ BestSeller", None))
        self.viBS_PB.setText(QCoreApplication.translate("MainWindow", u"Vincci BestSeller", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"ASH Reports", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Posting Date", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"End Date", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Stock As On", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Start Date", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Select Brand First Before Generating SQL Script ", None))
        self.jcCB.setText(QCoreApplication.translate("MainWindow", u"Jacadi", None))
        self.okCB.setText(QCoreApplication.translate("MainWindow", u"Okaidi", None))
        self.paCB.setText(QCoreApplication.translate("MainWindow", u"Parfois", None))
        self.uzCB.setText(QCoreApplication.translate("MainWindow", u"Undiz", None))
        self.viCB.setText(QCoreApplication.translate("MainWindow", u"Vincci", None))
        self.yrCB.setText(QCoreApplication.translate("MainWindow", u"Yevs", None))
        self.lsCB.setText(QCoreApplication.translate("MainWindow", u"LSR", None))
        self.stockPB.setText(QCoreApplication.translate("MainWindow", u"Stock SQL", None))
        self.salePB.setText(QCoreApplication.translate("MainWindow", u"Sale SQL", None))
        self.purchasePB.setText(QCoreApplication.translate("MainWindow", u"Purchase SQL", None))
        self.saleofferPB.setText(QCoreApplication.translate("MainWindow", u"Sale Offer SQL", None))
        self.itempricePB.setText(QCoreApplication.translate("MainWindow", u"Item Price SQL", None))
        self.firstpurchPB.setText(QCoreApplication.translate("MainWindow", u"First Purchase SQL", None))
        self.transferPB.setText(QCoreApplication.translate("MainWindow", u"Transfer Report", None))
        self.OfferItemPB.setText(QCoreApplication.translate("MainWindow", u"Active OfferItems", None))
        self.Rename_PB.setText(QCoreApplication.translate("MainWindow", u"Rename", None))
        self.SelectFolder_PB.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.label_25.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"SQL Scripts", None))
        self.lblURL.setText(QCoreApplication.translate("MainWindow", u"URL", None))
        self.lblUserID.setText(QCoreApplication.translate("MainWindow", u"User ID", None))
        self.lblPassword.setText(QCoreApplication.translate("MainWindow", u"Password", None))
        self.lblToken.setText(QCoreApplication.translate("MainWindow", u"Token", None))
        self.pbCRMToken.setText(QCoreApplication.translate("MainWindow", u"GetToken", None))
        self.pbDownloadReport.setText(QCoreApplication.translate("MainWindow", u"Get Sale Detail", None))
        self.pbCRMWebSC.setText(QCoreApplication.translate("MainWindow", u"Download Page Image", None))
        self.label_24.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"CRM Reports", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"Offer items", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Stock File", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Select File", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"Generate", None))
        self.pushButton_6.setText(QCoreApplication.translate("MainWindow", u"EDI2CSV", None))
        self.pushButton_12.setText(QCoreApplication.translate("MainWindow", u"ART2CSV", None))
        self.pushButton_7.setText(QCoreApplication.translate("MainWindow", u"Sale Summary", None))
        self.pushButton_8.setText(QCoreApplication.translate("MainWindow", u"Style Season", None))
        self.pushButton_9.setText(QCoreApplication.translate("MainWindow", u"Style Price", None))
        self.pushButton_10.setText(QCoreApplication.translate("MainWindow", u"For Margin", None))
        self.pushButton_11.setText(QCoreApplication.translate("MainWindow", u"Sale and Stock", None))
        self.pushButton_4.setText(QCoreApplication.translate("MainWindow", u"Online MP Sale", None))
        self.label_26.setText("")
        self.pushButton_5.setText(QCoreApplication.translate("MainWindow", u"SellThru", None))
        self.pushButton_13.setText(QCoreApplication.translate("MainWindow", u"Rename Art File", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Misc. Reports", None))
    # retranslateUi

