import polars as pl
import xlwings as xw
import os
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig

def startJacadiSellthruWorker(mw, progress_callback):
        all_text = ""
        # Get all user inputs
        saleFileDir = mw.saleReportPath_lineedit.text()
        stockFileDir = mw.stockReportPath_lineedit.text()
        masterFileDir = mw.masterFolderPath_lineedit.text()
        dataFileDir = mw.dataFolderPath_lineedit.text()
        # Initiate Class parameters
        initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
        merchWeek = mw.weekSelect_combobox.currentText()
        brand = mw.brandSelect_combobox.currentText()
        season = mw.seasonSelect_combobox.currentText()
        inputFile = os.path.join(mw.output_folder,"Combined","JC_Combined_Report.csv")
        all_text = all_text + f"Input File : {inputFile}\n"
        progress_callback.emit(all_text)
        path_exists = os.path.isfile(inputFile)
        # Sanity Checks
        if path_exists:
            if brand == "JC":
                if merchWeek != "All":
                    try:
                        app = xw.App(visible=False)
                        wb = xw.Book(mw.macroBook)
                        MakeJacadiSellThruReport_macro = wb.macro('JacadiSellThruReportNew')
                        all_text = all_text + "Jacadi SellThru Report Process Started\n"
                        progress_callback.emit(all_text)
                        MakeJacadiSellThruReport_macro(inputFile, season)
                        wb.close()
                        app.kill()
                        all_text = all_text + "Jacadi SellThru Report Process Ended\n"
                        progress_callback.emit(all_text)
                    except:
                        wb.close()
                        app.kill()
                        all_text = all_text + "Due to error ending Jacadi SellThru Report Process\n"
                        progress_callback.emit(all_text)
                else:
                    all_text = all_text + "Select Week Number\n"
                    progress_callback.emit(all_text)
            else:
                all_text = all_text + "Select Brand as Jacadi\n"
                progress_callback.emit(all_text)
        else:
            all_text = all_text + f"JC_AllMerged.csv file not available, first run brand report\n"
            progress_callback.emit(all_text)
        return "Done."