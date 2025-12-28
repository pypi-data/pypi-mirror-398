import xlwings as xw
import os
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.BrandFunctions import okaidiWeeklyBestSellerReport

def startOkaidiBestSellerWorker(mw, progress_callback):
    all_text = ""
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    imageDirectory = mw.imgFolderPath_lineedit.text()
    merchWeek = mw.weekSelect_combobox.currentText()
    brand = mw.brandSelect_combobox.currentText()
    inputFile = os.path.join(mw.output_folder,"StyleSummary","OK_AllMerged.csv")
    okBestSellerFile = os.path.join(mw.output_folder,"OK_BestSeller.csv")
    okBestSellerXLSXFile = os.path.join(mw.output_folder,"OK_BestSeller_Report.xlsx")
    all_text = all_text + f"Input File : {inputFile}\n"
    progress_callback.emit(all_text)
    path_exists = os.path.isfile(inputFile)
    # Sanity Checks
    if path_exists:
        if brand == "OK":
            if merchWeek != "All":
                try:
                    app = xw.App(visible=False)
                    wb = xw.Book(mw.macroBook)
                    MakeOkaidiBestSellerReport_macro = wb.macro('OkaidiBestSellerReport')
                    InsertImage_macro = wb.macro('InsertImage')
                    all_text = all_text + "Okaidi Best Seller Report Process Started\n"
                    progress_callback.emit(all_text)
                    bestSeller = okaidiWeeklyBestSellerReport(inputFile, merchWeek, "TY25")
                    bestSeller.write_csv(okBestSellerFile, separator=",")

                    if mw.okSaleItem_checkBox.isChecked():
                        saleitemyes = 1
                    else:
                        saleitemyes = 0

                    MakeOkaidiBestSellerReport_macro(okBestSellerFile, saleitemyes)
                    all_text = all_text + "Intermediate file created for BestSeller report\n"
                    progress_callback.emit(all_text)
                    wbs = xw.Book(okBestSellerXLSXFile)
                    count = wbs.sheets.count
                    wbs.close()
                    imageDirectory = imageDirectory + "\\"
                    all_text = all_text + f"Image Folder Path : {imageDirectory}\n"
                    progress_callback.emit(all_text)

                    for num in range(1,count+1):
                        InsertImage_macro(okBestSellerXLSXFile, imageDirectory, num, 1)
                        all_text = all_text + f"Inserting Images...\n"
                        progress_callback.emit(all_text)

                    wb.close()
                    app.kill()
                    all_text = all_text + "Okaidi Best Seller Report Process Ended\n"
                    progress_callback.emit(all_text)   
                except:
                    wb.close()
                    app.kill()
                    all_text = all_text + "Due to error ending Okaidi Best Seller Report Process\n"
                    progress_callback.emit(all_text)
                
            else:
                all_text = all_text + "Select Week Number\n"
                progress_callback.emit(all_text)
        else:
            all_text = all_text + "Select Brand as Okaidi\n"
            progress_callback.emit(all_text)
    else:
        all_text = all_text + f"OK_AllMerged.csv file not available, first run brand report\n"
        progress_callback.emit(all_text)
    return "Done."