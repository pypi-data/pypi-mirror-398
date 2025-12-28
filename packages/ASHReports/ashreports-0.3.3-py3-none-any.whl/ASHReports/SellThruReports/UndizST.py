import polars as pl
import xlwings as xw
import os
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig

def startUndizSellthruWorker(mw, progress_callback):
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
    inputFile = os.path.join(mw.output_folder,"Combined","UZ_Combined_Report.csv")
    stFile = os.path.join(mw.output_folder,"UZ_StockSellThruStore.csv")
    all_text = all_text + f"Input File : {inputFile}\n"
    progress_callback.emit(all_text)
    path_exists = os.path.isfile(inputFile)
    # Sanity Checks
    if path_exists:
        if brand == "UZ":
            if merchWeek != "All":
                try:
                    dfvi = pl.read_csv(inputFile, schema_overrides=ashc.dataTypeForAll).fill_null(0).fill_nan(0)
                    dfvi = dfvi.filter(pl.col('Season Code').is_in(mw.currentSeason))
                    dfvi = dfvi.filter(pl.col('Style Code').ne('All'))
                    dfvi = dfvi.with_columns((dfvi['ExchangeRate(AED)'] * dfvi['Cumm. SaleValue']).alias('Total Retail(AED)'))
                    dfvi = dfvi.with_columns((dfvi['ExchangeRate(AED)'] * dfvi['WTD SaleValue']).alias('LW SaleAmt(AED)'))
                    dfvi = dfvi.rename({'Cumm. SaleQty':'Total Sale Qty','WTD SaleQty':'LW SaleQty'})
                    dfSTvi = dfvi[['Brand Code','Country','ShortName','Item No_','Style Code','Colour Code','Size','Product Group','Item Category','Item Sub Class','Season Code','Unit Price','Current Price','Closing Stock','LW SaleQty','LW SaleAmt(AED)','Total Sale Qty','Total Retail(AED)']]
                    pidx = ["Brand Code","Country","ShortName","Style Code","Colour Code","Size","Product Group","Item Category","Item Sub Class","Season Code"]     # "Item No_"
                    pval = ['Total Sale Qty','Total Retail(AED)','LW SaleQty','LW SaleAmt(AED)','Closing Stock']      # "Total Sale Cost(AED)",'Total Cost(AED)'
                    dfSTvi = dfSTvi.group_by(pidx).agg(pl.sum(pval))
                    dfSTvi = dfSTvi.with_columns((dfSTvi['Total Sale Qty'] + dfSTvi['Closing Stock']).alias('Total Recvd Qty'))
                    dfSTvi.write_csv(stFile, separator=",")
                    app = xw.App(visible=False)
                    wb = xw.Book(mw.macroBook)
                    SellThru_macro = wb.macro('UndizSellThruReport')
                    all_text = all_text + "Undiz SellThru Report Process Started\n"
                    progress_callback.emit(all_text)
                    SellThru_macro(stFile, merchWeek)
                    wb.close()
                    app.kill()
                    all_text = all_text + "Undiz SellThru Report Process Ended\n"
                    progress_callback.emit(all_text)
                except:
                    wb.close()
                    app.kill()
                    all_text = all_text + "Due to error ending Vincci SellThru Report Process\n"
                    progress_callback.emit(all_text)
            else:
                all_text = all_text + "Select Week Number\n"
                progress_callback.emit(all_text)
        else:
            all_text = all_text + "Select Brand as Undiz\n"
            progress_callback.emit(all_text)
    else:
        all_text = all_text + f"UZ_Combined_Report.csv file not available, first run brand report\n"
        progress_callback.emit(all_text)
    return "Done."