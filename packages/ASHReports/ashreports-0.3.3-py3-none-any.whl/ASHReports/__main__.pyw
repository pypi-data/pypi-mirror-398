import sys, os, traceback, ctypes
import datetime as dt
from pathlib import Path
from ASHReports.ui_form import Ui_MainWindow
from PySide6.QtCore import QDate,QRunnable,Signal,QObject,Slot,QThreadPool
from PySide6.QtWidgets import QApplication,QMainWindow,QPushButton,QLineEdit,QTextEdit,QDateEdit,QFileDialog,QComboBox,QCheckBox,QMessageBox,QLabel,QSpinBox

import ASHReports.CombinedReports.JacadiCombined as JacadiCombined
import ASHReports.CombinedReports.OkaidiCombined as OkaidiCombined
import ASHReports.CombinedReports.ParfoisCombined as ParfoisCombined
import ASHReports.CombinedReports.UndizCombined as UndizCombined
import ASHReports.CombinedReports.VincciCombined as VincciCombined
import ASHReports.CombinedReports.YvesCombined as YvesCombined
import ASHReports.CombinedReports.LSRCombined as LSRCombined
import ASHReports.WeeklyReports.DesigualWeekly as DesigualWeekly
import ASHReports.WeeklyReports.JacadiWeekly as JacadiWeekly
import ASHReports.WeeklyReports.OkaidiWeekly as OkaidiWeekly
import ASHReports.WeeklyReports.ParfoisWeekly as ParfoisWeekly
import ASHReports.WeeklyReports.UndizWeekly as UndizWeekly
import ASHReports.WeeklyReports.VincciWeekly as VincciWeekly
import ASHReports.WeeklyReports.YvesWeekly as YvesWeekly
import ASHReports.WeeklyReports.LSRWeekly as LSRWeekly
import ASHReports.SellThruReports.JacadiST as JacadiST
import ASHReports.SellThruReports.OkaidiST as OkaidiST
import ASHReports.SellThruReports.ParfoisST as ParfoisST
import ASHReports.SellThruReports.UndizST as UndizST
import ASHReports.SellThruReports.VincciST as VincciST
import ASHReports.SellThruReports.YvesST as YvesST
import ASHReports.SellThruReports.LSRST as LSRST
import ASHReports.BestSellersReports.JacadiBestseller as JacadiBestseller
import ASHReports.BestSellersReports.OkaidiBestseller as OkaidiBestseller
import ASHReports.BestSellersReports.ParfoisBestseller as ParfoisBestseller
import ASHReports.BestSellersReports.UndizBestseller as UndizBestseller
import ASHReports.BestSellersReports.VincciBestseller as VincciBestseller
import ASHReports.StockReports.OkaidiStock as OkaidiStock
import ASHReports.UtilReports.sql as sql
import ASHReports.UtilReports.InsertImage as InsertImage
import ASHReports.UtilReports.art2_files as Art2CSVFiles
import ASHReports.UtilReports.salesummary as SaleSummary
import ASHReports.UtilReports.salenstock as SaleAndStock
import ASHReports.UtilReports.crmreports as CRMReports
import ASHReports.UtilReports.sellthru as SellThru
import ASHReports.UtilReports.margin_proj as MarginProj
import ASHReports.UtilReports.online_sale as MPOnline


class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(str)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dllPath = os.path.join(script_dir,"init_functions.dll")
        initDLL = ctypes.CDLL(dllPath)
        task_file_path = os.path.join(script_dir,"report_log.exe")
        
        # Define global variables
        self.counter = 0
        self.report_queue = []
        self.setWindowTitle("ASH Reports App")
        self.brandList = ['JC','OK','PA','UZ','VI','YR','LS']        # 
        self.brandList01 = ['JC','PA','UZ','VI','YR','LS']           # 
        self.yearList = ['2019','2020','2021','2022','2023','2024','2025','2026','2027']
        self.monthList = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

        self.exch_rate = {"AE":1.00000,"BH":9.74143,"OM":9.53929,"QA":1.00878,"KWT":12.00000}

        self.Sellthru_common_Seasons = {"2306":"24SS","2307":"24SS","2308":"24SS","2309":"24SS","2310":"24SS","2401":"24FW","2402":"24FW","2403":"24FW","2404":"24FW","2405":"24FW",
                                        "2406":"24FW","2407":"24FW","2408":"25SS","2409":"25SS","2410":"25SS","2411":"25SS","2412":"25SS","2501":"25SS","2502":"25FW","2503":"25FW",
                                        "2504":"25FW","2505":"25FW","2506":"25FW","2507":"25FW","2508":"25FW","2509":"25FW","2510":"25FW","2511":"25FW","2512":"26SS","2601":"26SS",
                                        "2602":"26SS","2603":"26SS","2604":"26SS","2605":"26SS","2606":"26SS","2023-1":"23SS","2023-2":"23FW","2024-1":"24SS","2024-2":"24FW",
                                        "2025-1":"25SS","2025-2":"25FW","2026-1":"26SS","2026-2":"26FW","24E":"24SS","24FW":"24FW","24H":"24FW","25E":"25SS","25H":"25FW","26E":"26SS",
                                        "26H":"26FW","24SS":"24SS","25SS":"25SS","25FW":"25FW","26SS":"26SS","26FW":"26FW","FLW":"25FW","NOS":"25FW"}

        self.Sellthru_Season_Filter = ["2401","2402","2403","2404","2405","2406","2407","2408","2409","2410","2411","2412","2501","2502","2503","2504","2505","2506","2507","2508",
                                       "2509","2510","2511","2512","2601","2602","2603","2604","2605","2606","2023-1","2023-2","2024-1","2024-2","2025-1","2025-2","2026-1","2026-2",
                                       "24E","24H","25E","25H","26E","26H","24FW","24SS","25FW","25SS","26SS","26FW","FLW","NOS"]

        self.Sellthru_Season_Remarks = {"Non Permanent":"Non Carryover","Non Carryover":"Non Carryover","Permanent":"Carryover","NA":"Non Carryover","Carryover":"Carryover",
                                        "Mini Product":"Carryover","Standard":"Carryover","Ramadan":"Non Carryover","":"Carryover","Sample":"Carryover","Mini-Produit":"Carryover",
                                        "Medium Product":"Carryover","Cleanser":"Carryover"}

        self.weekList = ['WK01','WK02','WK03','WK04','WK05','WK06','WK07','WK08','WK09','WK10','WK11','WK12','WK13','WK14','WK15','WK16','WK17','WK18','WK19','WK20','WK21','WK22',
                         'WK23','WK24','WK25','WK26','WK27','WK28','WK29','WK30','WK31','WK32','WK33','WK34','WK35','WK36','WK37','WK38','WK39','WK40','WK41','WK42','WK43','WK44',
                         'WK45','WK46','WK47','WK48','WK49','WK50','WK51','WK52','WK53']
        
        self.currentSeason = ["FLW","NOS","27FW","27SS","26FW","26SS","25FW","25SS","24FW","24SS","23FW","23SS","27H","27E","26H","26E","25H","25E","24H","24E","23H","23E","2023-2",
                              "2023-1","2024-1","2024-2","2025-1","2025-2","2026-1","2026-2","2027-1","2027-2","2712","2711","2710","2709","2708","2707","2706","2705","2704","2703",
                              "2702","2701","2612","2611","2610","2609","2608","2607","2606","2605","2604","2603","2602","2601","2512","2511","2510","2509","2508","2507","2506","2505",
                              "2504","2503","2502","2501","2412","2411","2410","2409","2408","2407","2406","2405","2404","2403","2402","2401","2312","2311","2310","2309","2308","2307",
                              "2306","2305","2304","2303","2302","2301"]
        
        # Intransit, Damage locations
        self.deleteStoreDisct = {"A01JC-TR":1,"A05JC-TR":1,"JC00":1,"JC05D":1,"YR99R":1,"YR99M":1,"A01YR-TR":1,"YR89":1,"YR99D":1,"A01VI-TR":1,"VI93":1,"A03VI-TR":1,"VI99R":1,
                                 "A02VI-TR":1,"VI99D":1,"VI99":1,"A06VI-TR":1,"VI00":1,"VI98":1,"A01UZ-TR":1,"UZ99R":1,"A03UZ-TR":1,"UZ00":1,"UZ98":1,"UZ99D":1,"A06PA-TR":1,
                                 "A05PA-TR":1,"A01PA-TR":1,"A03PA-TR":1,"PA23D":1,"PA98":1,"PA09D":1,"PA27D":1,"PA29D":1,"PA11D":1,"PA99D":1,"PA01D":1,"PA06D":1,"PA16D":1,
                                 "PA25D":1,"PA26D":1,"PA12D":1,"PA92":1,"PA15D":1,"PA24D":1,"PA31D":1,"A01OK-TR":1,"A02OK-TR":1,"A05OK-TR":1,"INTRANSIT":1,"A03OK-TR":1,
                                 "OK99R":1,"OK98":1,"OK00":1,"OK99D":1,"OK99T":1,"OK89":1,"OK90":1,"OK92":1,"OK98":1,"OK99S":1,"PA90":1,"UZ96":1,"JC03D":1,"JC02D":1,"PA03D":1,
                                 "PA19D":1,"PA20D":1,"PA28D":1,"PA30D":1}
        
        self.combined_report_columns = ["Brand Code","Country","City","Location Code","StoreName","ShortName","StoreSize","Location Type","Status","Division","Product Group",
                                   "Item Category","Item Class","Item Sub Class","Theme","RefCode","Style Code","First Purchase Date","Last Receive Date","Colour Code",
                                   "Size","Item No_","Season Code","Unit Price","Current Price","Unit Cost","ExchangeRate(AED)","Cumm. SaleQty","Cumm. CostValue",
                                   "Cumm. SaleValue","MTD SaleQty","MTD CostValue","MTD SaleValue","WTD SaleQty","WTD CostValue","WTD SaleValue","Closing Stock","StockCost",
                                   "StockRetail","StockOrgRetail","Purchased","Remarks","Combo2","Offer_Price","EOSS Discount","Disc.P"] # ,"Offer_Price","EOSS Discount","Disc%"
        
        self.output_folder = r"C:\Reports\Output"
        self.macroBook = r'C:\Reports\Data\Configs\Macro(ASH).xlsm'
        self.downloadFolder = "C:\\"
        self.saleOutFolder = r'C:\Reports\Data\SalesData'
        self.saleOfferFolder = r'C:\Reports\Data\SaleOffer'
        self.stockOutFolder = r'C:\Reports\Data\StockData'
        self.firstPurchOutFolder = r'C:\Reports\Data\FirstPurch'
        self.purchOutFolder = r'C:\Reports\Data\PurchaseData'
        self.default_folder = str(os.path.join(Path.home(), "Documents"))
        os.chdir("C:\\Reports")
        
        self.date_today = QDate.currentDate()
        self.date_noofdays = QDate.dayOfYear(self.date_today)
        self.date_day = QDate.day(self.date_today)
        self.date_month = QDate.month(self.date_today)
        self.date_year = QDate.year(self.date_today)
        self.date_ytdStartDate = QDate(self.date_year,1,1)
        self.date_mtdStartDate = QDate(self.date_year,self.date_month,1)
        self.date_lywtdStartDate = QDate(self.date_year -1, self.date_month, self.date_day)
        self.date_lywtdEndDate = QDate(self.date_year -1, self.date_month, self.date_day + 1)
        # Define Buttons
        self.processReport_button = self.findChild(QPushButton, "processReport_PB")
        self.weeklyReport_button = self.findChild(QPushButton, "weeklyReport_PB")
        self.consolidationReport_button = self.findChild(QPushButton, "consolidation_PB")
        self.comp_button = self.findChild(QPushButton, "comp_PB")
        self.close_button = self.findChild(QPushButton, "close_PB")
        self.selectSaleFolder_button = self.findChild(QPushButton, "selectSaleFolder_PB")
        self.selectStockFolder_button = self.findChild(QPushButton, "selectStockFolder_PB")
        self.selectMasterFolder_button = self.findChild(QPushButton, "selectMasterFolder_PB")
        self.selectDataFolder_button = self.findChild(QPushButton, "selectDataFolder_PB")
        self.okaidiSellthru_button = self.findChild(QPushButton, "okST_PB")
        self.okaidiBestseller_button = self.findChild(QPushButton, "okBS_PB")
        self.okaidiStockReport_button = self.findChild(QPushButton, "okSR_PB")
        self.selectImageFolder_button = self.findChild(QPushButton, "imgSelect_PB")
        self.insertImg_button = self.findChild(QPushButton, "insertImg_PB")
        self.vincciSellthru_button = self.findChild(QPushButton, "viST_PB")
        self.vincciBestseller_button = self.findChild(QPushButton, "viBS_PB")
        self.undizSellthru_button = self.findChild(QPushButton, "uzST_PB")
        self.undizBestseller_button = self.findChild(QPushButton, "uzBS_PB")
        self.jacadiSellthru_button = self.findChild(QPushButton, "jcST_PB")
        self.parfoisNewSellthru_button = self.findChild(QPushButton, "paNST_PB")
        self.parfoisNewStock_button = self.findChild(QPushButton, "paNStk_PB")
        self.misc_offerfolder_button = self.findChild(QPushButton, "pushButton")
        self.misc_stockfolder_button = self.findChild(QPushButton, "pushButton_2")
        self.misc_generate_button = self.findChild(QPushButton, "pushButton_3")#
        self.onlineMP_button = self.findChild(QPushButton, "pushButton_4")#     
        self.sellthru_button = self.findChild(QPushButton, "pushButton_5")#
        self.edi2csv_button = self.findChild(QPushButton, "pushButton_6")
        self.salesummary_button = self.findChild(QPushButton, "pushButton_7")
        self.styleseason_button = self.findChild(QPushButton, "pushButton_8")
        self.styleprice_button = self.findChild(QPushButton, "pushButton_9")
        self.marginProj_button = self.findChild(QPushButton, "pushButton_10")#
        self.saleandstock_button = self.findChild(QPushButton, "pushButton_11")
        self.art2csv_button = self.findChild(QPushButton, "pushButton_12")
        self.renameArt_button = self.findChild(QPushButton, "pushButton_13")
        self.crmToken_button = self.findChild(QPushButton, "pbCRMToken")
        self.crmDownload_button = self.findChild(QPushButton, "pbDownloadReport")
        self.crmSC_button = self.findChild(QPushButton, "pbCRMWebSC")
        # Define text and line edits
        self.output_textedit = self.findChild(QTextEdit, "outpout_TE")
        self.saleReportPath_lineedit = self.findChild(QLineEdit, "saleReportPath_LE")
        self.saleReportPath_lineedit.setText(r"C:\Reports\Data\SalesData")
        self.stockReportPath_lineedit = self.findChild(QLineEdit, "stockReportPath_LE")
        self.stockReportPath_lineedit.setText(r"C:\Reports\Data\StockData")
        self.masterFolderPath_lineedit = self.findChild(QLineEdit, "masterFilePath_LE")
        self.masterFolderPath_lineedit.setText(r"C:\Reports\Data\MasterFiles")
        self.dataFolderPath_lineedit = self.findChild(QLineEdit, "dataFilesPath_LE")
        self.dataFolderPath_lineedit.setText(r"C:\Reports\Data")
        self.imgFolderPath_lineedit = self.findChild(QLineEdit, "imgFolderPath_LE")
        self.imgFolderPath_lineedit.setText(r"C:\Reports\Data\Images\Okaidi")
        self.infotextcrm_lable = self.findChild(QLabel, "label_24")
        self.infotextcrm_lable.setText(r"")
        self.miscofferFolderPath_lineedit = self.findChild(QLineEdit, "lineEdit")
        self.miscstockFolderPath_lineedit = self.findChild(QLineEdit, "lineEdit_2")
        self.infotextmisc_lable = self.findChild(QLabel, "label_26")
        self.infotextmisc_lable.setText(r"")
        self.crmUrl_lineedit = self.findChild(QLineEdit, "leURL")
        self.crmUrl_lineedit.setText(r"https://asp.adelya.com/loyaltyoperator/login.jsp")
        self.crmUserID_lineedit = self.findChild(QLineEdit, "leUserID")
        self.crmUserID_lineedit.setText(r"")
        self.crmPassword_lineedit = self.findChild(QLineEdit, "lePassword")
        self.crmPassword_lineedit.setText(r"")
        self.crmToken_lineedit = self.findChild(QLineEdit, "leToken")
        #self.crmToken_lineedit.setText(r"")

        # Define Date edits
        self.ytdStart_dateedit = self.findChild(QDateEdit, "ytdStart_DE")
        self.ytdStart_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.ytdEnd_dateedit = self.findChild(QDateEdit, "ytdEnd_DE")
        self.ytdEnd_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.mtdStart_dateedit = self.findChild(QDateEdit, "mtdStart_DE")
        self.mtdStart_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.mtdEnd_dateedit = self.findChild(QDateEdit, "mtdEnd_DE")
        self.mtdEnd_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.wtdStart_dateedit = self.findChild(QDateEdit, "wtdStart_DE")
        self.wtdStart_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.wtdEnd_dateedit = self.findChild(QDateEdit, "wtdEnd_DE")
        self.wtdEnd_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.lywtdStart_dateedit = self.findChild(QDateEdit, "lywtdStart_DE")
        self.lywtdStart_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.lywtdEnd_dateedit = self.findChild(QDateEdit, "lywtdEnd_DE")
        self.lywtdEnd_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.miscStart_dateedit = self.findChild(QDateEdit, "dateEdit_3")
        self.miscStart_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.miscEnd_dateedit = self.findChild(QDateEdit, "dateEdit_4")
        self.miscEnd_dateedit.setDisplayFormat("d-MMM-yyyy")
        self.crmStart_dateedit = self.findChild(QDateEdit, "dateEdit")
        self.crmStart_dateedit.setDisplayFormat("yyyy-MM-dd")
        self.crmEnd_dateedit = self.findChild(QDateEdit, "dateEdit_2")
        self.crmEnd_dateedit.setDisplayFormat("yyyy-MM-dd")

        self.ytdStart_dateedit.setDate(self.date_ytdStartDate)
        self.mtdStart_dateedit.setDate(self.date_mtdStartDate)
        self.wtdStart_dateedit.setDate(self.date_today.addDays(-7))
        self.lywtdStart_dateedit.setDate(self.date_lywtdStartDate.addDays(-7))
        self.ytdEnd_dateedit.setDate(self.date_today)
        self.mtdEnd_dateedit.setDate(self.date_today)
        self.wtdEnd_dateedit.setDate(self.date_today)
        self.lywtdEnd_dateedit.setDate(self.date_lywtdEndDate)
        self.miscStart_dateedit.setDate(self.date_ytdStartDate)
        self.miscEnd_dateedit.setDate(self.date_today)
        self.crmStart_dateedit.setDate(self.date_ytdStartDate)
        self.crmEnd_dateedit.setDate(self.date_today)

        # Define combo box
        self.weekSelect_combobox = self.findChild(QComboBox, "selectWeek_CB")
        self.weekSelect_combobox.addItems(['All'] + self.weekList)
        self.brandSelect_combobox = self.findChild(QComboBox, "selectBrand_CB")
        self.brandSelect_combobox.addItems(['All'] + self.brandList)
        self.seasonSelect_combobox = self.findChild(QComboBox, "selectSeason_CB")
        self.seasonSelect_combobox.addItems(['All'] + self.currentSeason)
        self.miscbrandSelect_combobox = self.findChild(QComboBox, "comboBox")
        self.miscbrandSelect_combobox.addItems(self.brandList)

        # Define Check Box
        self.semidetail_checkBox = self.findChild(QCheckBox, "semiDetail_cBox")
        self.summary_checkBox = self.findChild(QCheckBox, "summary_cBox")
        self.okSaleItem_checkBox = self.findChild(QCheckBox, "okSaleItem_cBox")
        # Define button press actions
        self.selectSaleFolder_button.clicked.connect(self.selectSaleFolder)
        self.selectStockFolder_button.clicked.connect(self.selectStockFolder)
        self.selectMasterFolder_button.clicked.connect(self.selectMasterFolder)
        self.selectDataFolder_button.clicked.connect(self.selectDataFolder)
        self.processReport_button.clicked.connect(self.startCombinedReport)
        self.weeklyReport_button.clicked.connect(self.startWeeklyReport)
        self.okaidiSellthru_button.clicked.connect(self.startOkaidiSellthru)
        self.okaidiBestseller_button.clicked.connect(self.startOkaidiBestSeller)
        self.okaidiStockReport_button.clicked.connect(self.startOkaidiStockReport)
        self.selectImageFolder_button.clicked.connect(self.selectImageFolder)
        self.insertImg_button.clicked.connect(self.startInsertImageWorker)
        self.vincciBestseller_button.clicked.connect(self.startVincciBestSeller)
        self.vincciSellthru_button.clicked.connect(self.startVincciSellthru)
        self.undizBestseller_button.clicked.connect(self.startUndizBestSeller)
        self.undizSellthru_button.clicked.connect(self.startUndizSellthru)
        self.jacadiSellthru_button.clicked.connect(self.startJacadiSellthru)
        self.parfoisNewSellthru_button.clicked.connect(self.startParfoisSellthru)
        self.parfoisNewStock_button.clicked.connect(self.startParfoisBestSeller)
        self.close_button.clicked.connect(self.closeApplication)
        self.art2csv_button.clicked.connect(self.art2csvWorker)
        self.edi2csv_button.clicked.connect(self.edi2csvWorker)
        self.onlineMP_button.clicked.connect(self.onlineMPReportWorker)
        self.sellthru_button.clicked.connect(self.sellthruReportWorker)
        self.marginProj_button.clicked.connect(self.marginProjWorker)
        self.renameArt_button.clicked.connect(self.rename_art_files_Worker)
        self.salesummary_button.clicked.connect(self.salesummaryWorker)
        self.saleandstock_button.clicked.connect(self.startsalenstock)
        self.styleprice_button.clicked.connect(self.startstyleprice)
        self.styleseason_button.clicked.connect(self.startstyleseason)
        self.crmDownload_button.clicked.connect(self.startcrmreport)
        self.crmToken_button.clicked.connect(self.startcrmgettoken)
        #------------------------------------------- SQL Gen --------------------------------------------------------
        self.ItemLedgerEntryType = {'Purchase':0,'Sales':1,'POS Adjustment':2,'Neg Adjustment':3,'Transfer':4,'Opening Stock':5}
        self.ExchangeRatestoAED = {'UAE':1.00000,'QTR':1.00878,'OMN':9.53929,'BAH':9.74143,'KWT':12.00000}
        self.dbFiles = {'A01JC - Jacadi UAE':'JC','A05JC - Jacadi KWT':'JC','A01OK - Okaidi Obaibi UAE':'OK','A02OK - Okaidi Obaibi QTR':'OK','A05OK - Okaidi Obaibi KWT':'OK','A03OK - Okaidi Obaibi OMN':'OK','A06OK - Okaidi Obaibi BAH':'OK','A01PA - Parfois UAE':'PA','A06PA - Parfois BAH':'PA','A03PA - Parfois OMN':'PA','A05PA - Parfois KWT':'PA','A01UZ - Undiz UAE':'UZ','A03UZ - Undiz OMN':'UZ','A01VI - Vincci UAE':'VI','A03VI - Vincci OMN':'VI','A06VI - Vincci BAH':'VI','A02VI - Vincci QTR':'VI','A01YR - Yves Rocher UAE':'YR','A01LS - La Savonnerie Royl UAE':'LS'}
        self.outFolderSale = os.path.join(self.downloadFolder, "SQL")
        self.outFolderStock = os.path.join(self.downloadFolder, "SQL")
        self.outFolderFirstPurchase = os.path.join(self.downloadFolder, "SQL")
        self.outFolderPruchase = os.path.join(self.downloadFolder, "SQL")
        self.outFolderTransaction = os.path.join(self.downloadFolder, "SQL")
        self.outFolderSaleOffer = os.path.join(self.downloadFolder, "SQL")
        self.outFolderCombined = os.path.join(self.downloadFolder, "SQL")
        # Define text and line edits
        self.dumpFolderPath_lineedit = self.findChild(QLineEdit, "dumpFolder_LE")
        self.infotextsql_lable = self.findChild(QLabel, "label_25")
        self.infotextsql_lable.setText(r"")
        # Define Check Box
        self.jacadi_checkBox = self.findChild(QCheckBox, "jcCB")
        self.okaidi_checkBox = self.findChild(QCheckBox, "okCB")
        self.parfois_checkBox = self.findChild(QCheckBox, "paCB")
        self.undiz_checkBox = self.findChild(QCheckBox, "uzCB")
        self.vincci_checkBox = self.findChild(QCheckBox, "viCB")
        self.yves_checkBox = self.findChild(QCheckBox, "yrCB")
        self.lsr_checkBox = self.findChild(QCheckBox, "lsCB")
        # Define Buttons
        self.stock_button = self.findChild(QPushButton, "stockPB")
        self.sale_button = self.findChild(QPushButton, "salePB")
        self.firstpurch_button = self.findChild(QPushButton, "firstpurchPB")
        self.itemprice_button = self.findChild(QPushButton, "itempricePB")
        self.purchase_button = self.findChild(QPushButton, "purchasePB")
        self.saleoffer_button = self.findChild(QPushButton, "saleofferPB")
        self.selectFolder_button = self.findChild(QPushButton, "SelectFolder_PB")
        self.rename_button = self.findChild(QPushButton, "Rename_PB")
        self.transfer_button = self.findChild(QPushButton, "transferPB")
        self.activeOffer_button = self.findChild(QPushButton, "OfferItemPB")
        # Define button press actions
        self.stock_button.clicked.connect(self.startstockSQL)
        self.sale_button.clicked.connect(self.startsaleSQL)
        self.firstpurch_button.clicked.connect(self.startfirstpurchaseSQL)
        self.itemprice_button.clicked.connect(self.startItempriceSQL)
        self.purchase_button.clicked.connect(self.startpurchaseSQL)
        self.saleoffer_button.clicked.connect(self.startsaleofferSQL)
        self.selectFolder_button.clicked.connect(self.startselectDumpFolder)
        self.rename_button.clicked.connect(self.startrenameDumpFiles)
        self.transfer_button.clicked.connect(self.starttransferSQL)
        self.activeOffer_button.clicked.connect(self.startactiveOfferItemSQL)

        self.dtDate = self.date_today.toPython()
        self.fileName = f"CSVFile_{self.dtDate}T*.csv"
        self.selected_folder = os.path.join(self.default_folder, self.fileName)
        self.dumpFolderPath_lineedit.setText(self.selected_folder)

        self.date_startDate = QDate(self.date_year,1,1)
        self.date_stkDate = QDate(self.date_year, self.date_month, self.date_day - 1)

        self.stkStart_dateedit = self.findChild(QDateEdit, "stkStartDE")
        self.stkStart_dateedit.setDisplayFormat("dd-MMM-yyyy")
        self.stkEnd_dateedit = self.findChild(QDateEdit, "stkEndDE")
        self.stkEnd_dateedit.setDisplayFormat("dd-MMM-yyyy")

        self.slsStart_dateedit = self.findChild(QDateEdit, "slsStartDE")
        self.slsStart_dateedit.setDisplayFormat("dd-MMM-yyyy")
        self.slsEnd_dateedit = self.findChild(QDateEdit, "slsEndDE")
        self.slsEnd_dateedit.setDisplayFormat("dd-MMM-yyyy")

        self.stkStart_dateedit.setDate(self.date_today)
        self.stkEnd_dateedit.setDate(self.date_stkDate)
        self.slsStart_dateedit.setDate(self.date_startDate)
        self.slsEnd_dateedit.setDate(self.date_today)
        #------------------------------------------------------------------------------------------------------------
        initDLL.Init_module()
        print(f"Result: {initDLL.create_task(task_file_path.encode('utf-8'))}")
        self.threadpool = QThreadPool()

    def startsalenstock(self):        # Pass the function to execute
        worker = Worker(SaleAndStock.SaleAndStockReport, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startstyleprice(self):        # Pass the function to execute
        worker = Worker(SaleAndStock.StyleAndPriceReport, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startstyleseason(self):        # Pass the function to execute
        worker = Worker(SaleAndStock.StyleAndSeasonReport, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startcrmreport(self):        # Pass the function to execute
        worker = Worker(CRMReports.CRMReport, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startcrmgettoken(self):        # Pass the function to execute
        worker = Worker(CRMReports.CRMGetToken, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startstockSQL(self):        # Pass the function to execute
        worker = Worker(sql.stockSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startsaleSQL(self):        # Pass the function to execute
        worker = Worker(sql.saleSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startfirstpurchaseSQL(self):        # Pass the function to execute
        worker = Worker(sql.firstpurchaseSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startItempriceSQL(self):        # Pass the function to execute
        worker = Worker(sql.itempriceSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startpurchaseSQL(self):        # Pass the function to execute
        worker = Worker(sql.purchaseSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startsaleofferSQL(self):        # Pass the function to execute
        worker = Worker(sql.saleofferSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startselectDumpFolder(self):        # Pass the function to execute
        self.dtDate = self.date_today.toPython()
        self.fileName = f"CSVFile_{self.dtDate}T*.csv"
        self.file_path, _ = QFileDialog.getOpenFileName(self, 'Pick Dump file')
        self.folder_path = os.path.dirname(os.path.abspath(self.file_path))
        self.selected_folder = os.path.join(self.folder_path, self.fileName)
        self.dumpFolderPath_lineedit.setText(f"{self.selected_folder}")

    def startrenameDumpFiles(self):        # Pass the function to execute
        worker = Worker(sql.renameDumpFiles, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def starttransferSQL(self):        # Pass the function to execute
        worker = Worker(sql.transferSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def startactiveOfferItemSQL(self):        # Pass the function to execute
        worker = Worker(sql.activeOfferItemSQL, self)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)   # Execute

    def selectSaleFolder(self):
        self.file_path, self.filter_ = QFileDialog.getOpenFileName(self, 'Pick Sale file')
        self.folder_path = os.path.dirname(os.path.abspath(self.file_path))
        self.saleReportPath_lineedit.setText(f"{self.folder_path}")

    def selectStockFolder(self):
        self.file_path, self.filter_ = QFileDialog.getOpenFileName(self, 'Pick Stock file')
        self.folder_path = os.path.dirname(os.path.abspath(self.file_path))
        self.stockReportPath_lineedit.setText(f"{self.folder_path}")

    def selectMasterFolder(self):
        self.file_path, self.filter_ = QFileDialog.getOpenFileName(self, 'Pick Master file')
        self.folder_path = os.path.dirname(os.path.abspath(self.file_path))
        self.masterFolderPath_lineedit.setText(f"{self.folder_path}")

    def selectDataFolder(self):
        self.file_path, self.filter_ = QFileDialog.getOpenFileName(self, 'Pick Data file')
        self.folder_path = os.path.dirname(os.path.abspath(self.file_path))
        self.dataFolderPath_lineedit.setText(f"{self.folder_path}")

    def selectImageFolder(self):
        self.file_path, self.filter_ = QFileDialog.getOpenFileName(self, 'Pick Image file')
        self.folder_path = os.path.dirname(os.path.abspath(self.file_path))
        self.imgFolderPath_lineedit.setText(f"{self.folder_path}")

    def startJacadiSellthru(self):
        # Pass the function to execute
        worker = Worker(JacadiST.startJacadiSellthruWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startOkaidiStockReport(self):
        # Pass the function to execute
        worker = Worker(OkaidiStock.startOkaidiStockReportWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startOkaidiSellthru(self):
        # Pass the function to execute
        worker = Worker(OkaidiST.startOkaidiSellthruWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startOkaidiBestSeller(self):
        # Pass the function to execute
        worker = Worker(OkaidiBestseller.startOkaidiBestSellerWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startVincciSellthru(self):
        # Pass the function to execute
        worker = Worker(VincciST.startVincciSellthruWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startVincciBestSeller(self):
        # Pass the function to execute
        worker = Worker(VincciBestseller.startVincciBestSellerWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startUndizSellthru(self):
        # Pass the function to execute
        worker = Worker(UndizST.startUndizSellthruWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startUndizBestSeller(self):
        # Pass the function to execute
        worker = Worker(UndizBestseller.startUndizBestSellerWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startParfoisSellthru(self):
        # Pass the function to execute
        worker = Worker(ParfoisST.startParfoisSellthruWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startParfoisBestSeller(self):
        # Pass the function to execute
        worker = Worker(ParfoisBestseller.startParfoisBestSellerWorker, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def startCombinedReport(self):
        self.brand = self.brandSelect_combobox.currentText()
        if self.brand == "All":
            self.report_queue = [
                JacadiCombined.startCombinedReportWorker,
                OkaidiCombined.startCombinedReportWorker,
                ParfoisCombined.startCombinedReportWorker,
                UndizCombined.startCombinedReportWorker,
                VincciCombined.startCombinedReportWorker,
                YvesCombined.startCombinedReportWorker,
                LSRCombined.startCombinedReportWorker,
            ]
            self.runNextReport()

        elif self.brand == "JC":
            worker = Worker(JacadiCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "OK":
            worker = Worker(OkaidiCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "PA":
            worker = Worker(ParfoisCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "UZ":
            worker = Worker(UndizCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "VI":
            worker = Worker(VincciCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "YR":
            worker = Worker(YvesCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "LS":
            worker = Worker(LSRCombined.startCombinedReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        else:
            pass

    def startWeeklyReport(self):
        self.brand = self.brandSelect_combobox.currentText()
        if self.brand == "All":
            self.report_queue = [
                DesigualWeekly.startWeeklyReportWorker,
                JacadiWeekly.startWeeklyReportWorker,
                OkaidiWeekly.startWeeklyReportWorker,
                ParfoisWeekly.startWeeklyReportWorker,
                UndizWeekly.startWeeklyReportWorker,
                VincciWeekly.startWeeklyReportWorker,
                YvesWeekly.startWeeklyReportWorker,
                LSRWeekly.startWeeklyReportWorker,
            ]
            self.runNextReport()

        elif self.brand == "DE":
            worker = Worker(DesigualWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "JC":
            worker = Worker(JacadiWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "OK":
            worker = Worker(OkaidiWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "PA":
            worker = Worker(ParfoisWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "UZ":
            worker = Worker(UndizWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "VI":
            worker = Worker(VincciWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "YR":
            worker = Worker(YvesWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        elif self.brand == "LS":
            worker = Worker(LSRWeekly.startWeeklyReportWorker,self)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.progress_fn)
            self.threadpool.start(worker)
        else:
            pass

    def runNextReport(self):
        if not self.report_queue:
            self.progress_fn("All reports finished.")
            self.thread_complete()
            return

        report_function = self.report_queue.pop(0)
        worker = Worker(report_function, self)
        worker.signals.progress.connect(self.progress_fn)
        worker.signals.finished.connect(self.runNextReport)
        worker.signals.error.connect(self.report_error)
        self.threadpool.start(worker)

    def report_error(self, error_tuple):
        traceback_str = error_tuple[2]
        self.progress_fn(f"ERROR: {error_tuple[0].__name__}: {error_tuple[1]}\n{traceback_str}")
        self.report_queue.clear()
        self.progress_fn("Report queue cleared due to an error.")

    def startInsertImageWorker(self):
        # Pass the function to execute
        self.file_path, filter_ = QFileDialog.getOpenFileName(self, 'Select the file to insert Image')
        worker = Worker(InsertImage.insertImage, self, self.file_path)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def art2csvWorker(self):
        # Pass the function to execute
        self.file_path, _ = QFileDialog.getOpenFileName(self, 'Select the Art2 file', 'C:/', 'dat Files (*.dat);;All Files (*.*)')
        self.fPath = os.path.dirname(os.path.abspath(self.file_path))
        worker = Worker(Art2CSVFiles.Art2CSV, self, self.fPath)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def edi2csvWorker(self):
        # Pass the function to execute
        self.file_path, filter_ = QFileDialog.getOpenFileName(self, 'Select the FPRICAT file', 'C:/', 'dat Files (*.edi);;All Files (*.*)')
        self.fPath = os.path.dirname(os.path.abspath(self.file_path))
        worker = Worker(Art2CSVFiles.EDI2CSV, self, self.fPath)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def rename_art_files_Worker(self):
        # Pass the function to execute
        self.file_path, filter_ = QFileDialog.getOpenFileName(self, 'Select the Art file', 'C:/', 'dat Files (*.edi);;All Files (*.*)')
        self.fPath = os.path.dirname(os.path.abspath(self.file_path))
        worker = Worker(Art2CSVFiles.rename_art_files, self, self.fPath)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)
    
    def salesummaryWorker(self):
        worker = Worker(SaleSummary.SaleSummary, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def sellthruReportWorker(self):
        worker = Worker(SellThru.WeeklySellThruReport, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def marginProjWorker(self):
        worker = Worker(MarginProj.MarginProjection, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def onlineMPReportWorker(self):
        worker = Worker(MPOnline.OnlineMPReport, self)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def closeApplication(self):
        sys.exit(app.exec())

    def thread_complete(self):
        print("Thread completed!")

    def progress_fn(self, msg):
        self.output_textedit.setText(msg)


if __name__ == "__main__":
    last = dt.date(2026, 2, 28)
    tod = dt.date.today()
    currDir = os.getcwd()
    if (tod > last):
        sys.exit(0)
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
