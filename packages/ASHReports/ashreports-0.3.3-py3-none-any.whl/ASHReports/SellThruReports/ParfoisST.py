import polars as pl
import xlwings as xw
import os
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig

def startParfoisSellthruWorker(mw, progress_callback):
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
    inputFile = os.path.join(mw.output_folder,"Combined","PA_Combined_Report.csv")
    stFile = os.path.join(mw.output_folder,"PA_StockSellThruStore.csv")
    all_text = all_text + f"Input File : {inputFile}\n"
    progress_callback.emit(all_text)
    path_exists = os.path.isfile(inputFile)
    # Sanity Checks
    if path_exists:
        if brand == "PA":
            if merchWeek != "All":
                try:
                    dfpa = pl.read_csv(inputFile,schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0)
                    dfpa = dfpa.filter(pl.col('Season Code').is_in(mw.currentSeason))
                    #dfpa = dfpa.with_columns((dfpa['Cumm. SaleValue'] + dfpa['MTD SaleValue'] + dfpa['WTD SaleValue'] + dfpa['StockRetail'] + dfpa['StockOrgRetail']).alias('ZeroFilter'))
                    dfpa = dfpa.with_columns((dfpa['Cumm. SaleQty'].abs() + dfpa['Cumm. CostValue'].abs() + dfpa['MTD SaleQty'].abs() + dfpa['WTD SaleQty'].abs() + dfpa['Closing Stock'].abs() + dfpa['StockCost'].abs()).alias('ZeroFilter'),)
                    dfpa = dfpa.filter(pl.col('ZeroFilter').ne(0))
                    dfpa = dfpa.filter(pl.col('Style Code').ne('All'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['Cumm. SaleValue']).alias('Total Retail(AED)'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['Cumm. CostValue']).alias('Total Cost(AED)'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['WTD SaleValue']).alias('LW SaleAmt(AED)'))
                    dfpa = dfpa.with_columns((dfpa['Unit Price'] * dfpa['Cumm. SaleQty'] * dfpa['ExchangeRate(AED)']).alias('Total OrgRetail(AED)'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['StockCost']).alias('StockCost(AED)'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['StockRetail']).alias('StockRetail(AED)'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['StockOrgRetail']).alias('StockOrgRetail(AED)'))
                    dfpa = dfpa.rename({'Cumm. SaleQty':'Total Sale Qty','WTD SaleQty':'LW SaleQty'})

                    dfSTpa = dfpa[["Brand Code","Country","ShortName","Item No_","Style Code","Colour Code","Size","Division","Product Group","Item Category","Item Class","Season Code","Theme","Remarks","Unit Price","Current Price","ExchangeRate(AED)","Closing Stock","LW SaleQty","LW SaleAmt(AED)","Total Sale Qty","Total Retail(AED)","Total Cost(AED)","Total OrgRetail(AED)","StockCost(AED)","StockRetail(AED)","StockOrgRetail(AED)"]]

                    pidx = ["Brand Code","Country","ShortName","Style Code","Colour Code","Size","Division","Product Group","Item Category","Item Class","Season Code","Theme","Remarks"]     # "Item No_"
                    pval = ["Total Sale Qty","Total Cost(AED)","Total Retail(AED)","Total OrgRetail(AED)","LW SaleQty","LW SaleAmt(AED)","Closing Stock","StockCost(AED)","StockRetail(AED)","StockOrgRetail(AED)"]      # "Total Sale Cost(AED)",'Total Cost(AED)'
                    dfSTpa = dfSTpa.group_by(pidx).agg(pl.sum(pval))
                    dfSTpa = dfSTpa.with_columns((dfSTpa['Total Sale Qty'] + dfSTpa['Closing Stock']).alias('Total Recvd Qty'))
                    dfSTpa = dfSTpa.with_columns((dfSTpa['Total Cost(AED)'] + dfSTpa['StockCost(AED)']).alias('Total Recvd Cost(AED)'))
                    dfSTpa = dfSTpa.with_columns((dfSTpa['Total OrgRetail(AED)'] + dfSTpa['StockOrgRetail(AED)']).alias('Total Recvd Org. Retail(AED)'))
                    dfSTpa.write_csv(stFile, separator=",")
                    app = xw.App(visible=False)
                    wb = xw.Book(mw.macroBook)
                    SellThru_macro = wb.macro('ParfoisSellThruReportNew')
                    all_text = all_text + "Parfois SellThru Report Process Started\n"
                    progress_callback.emit(all_text)
                    SellThru_macro(stFile, merchWeek)
                    wb.close()
                    app.kill()
                    all_text = all_text + "Parfois SellThru Report Process Ended\n"
                    progress_callback.emit(all_text)
                except:
                    wb.close()
                    app.kill()
                    all_text = all_text + "Due to error ending Parfois SellThru Report Process\n"
                    progress_callback.emit(all_text)
            else:
                all_text = all_text + "Select Season Code\n"
                progress_callback.emit(all_text)
        else:
            all_text = all_text + "Select Brand as Parfois\n"
            progress_callback.emit(all_text)
    else:
        all_text = all_text + f"PA_Combined_Report.csv file not available, first run brand report\n"
        progress_callback.emit(all_text)
    return "Done."