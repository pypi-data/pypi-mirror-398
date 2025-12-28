import xlwings as xw
import polars as pl
import os
from ASHC_v3.initiateConfig import initiateConfig


def startParfoisBestSellerWorker(mw, progress_callback):
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
    stFile = os.path.join(mw.output_folder,"PA_BestSeller.csv")
    all_text = all_text + f"Input File : {inputFile}\n"
    progress_callback.emit(all_text)
    path_exists = os.path.isfile(inputFile)
    # Sanity Checks
    if path_exists:
        if brand == "PA":
            if merchWeek != "All":
                try:
                    dfpa = pl.read_csv(inputFile,infer_schema_length=10000,).fill_null(0).fill_nan(0)
                    #dfpa = dfpa.with_columns((dfpa['Cumm. SaleValue'] + dfpa['MTD SaleValue'] + dfpa['WTD SaleValue'] + dfpa['StockRetail'] + dfpa['StockOrgRetail']).alias('ZeroFilter'))
                    dfpa = dfpa.with_columns((dfpa['Cumm. SaleQty'].abs() + dfpa['Cumm. CostValue'].abs() + dfpa['MTD SaleQty'].abs() + dfpa['WTD SaleQty'].abs() + dfpa['Closing Stock'].abs() + dfpa['StockCost'].abs()).alias('ZeroFilter'),)
                    dfpa = dfpa.filter(pl.col('ZeroFilter').ne(0))
                    dfpa = dfpa.filter(pl.col('Style Code').ne('All'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['Cumm. SaleValue']).alias('Total Retail(AED)'))
                    dfpa = dfpa.with_columns((dfpa['ExchangeRate(AED)'] * dfpa['WTD SaleValue']).alias('LW SaleAmt(AED)'))
                    dfpa = dfpa.rename({'Cumm. SaleQty':'Total Sale Qty','WTD SaleQty':'LW SaleQty'})
                    dfSTpa = dfpa[['Brand Code','Country','ShortName','Item No_','Style Code','Colour Code','Size','Division','Product Group','Item Category','Item Class','Season Code',"Theme","Remarks",'Unit Price','Current Price','Closing Stock','LW SaleQty','LW SaleAmt(AED)','Total Sale Qty','Total Retail(AED)']]
                    pidx = ["Brand Code","Country","ShortName","Item No_","Style Code","Colour Code","Size","Division","Product Group","Item Category","Item Class","Season Code","Theme","Remarks"]     # 
                    pval = ['Total Sale Qty','Total Retail(AED)','LW SaleQty','LW SaleAmt(AED)','Closing Stock']      # "Total Sale Cost(AED)",'Total Cost(AED)'
                    dfSTpa = dfSTpa.group_by(pidx).agg(pl.sum(pval))
                    dfSTpa = dfSTpa.with_columns((dfSTpa['Total Sale Qty'] + dfSTpa['Closing Stock']).alias('Total Recvd Qty'))
                    dfSTpa.write_csv(stFile, separator=",")
                    app = xw.App(visible=False)
                    wb = xw.Book(mw.macroBook)
                    BestSeller_macro = wb.macro('ParfoisBestSellerReportNew')
                    all_text = all_text + "Parfois BestSeller Report Process Started\n"
                    progress_callback.emit(all_text)
                    BestSeller_macro(stFile, merchWeek)
                    wb.close()
                    app.kill()
                    all_text = all_text + "Parfois BestSeller Report Process Ended\n"
                    progress_callback.emit(all_text)
                except:
                    wb.close()
                    app.kill()
                    all_text = all_text + "Due to error ending Parfois BestSeller Report Process\n"
                    progress_callback.emit(all_text)
            else:
                all_text = all_text + "Select Week Number\n"
                progress_callback.emit(all_text)
        else:
            all_text = all_text + "Select Brand as Parfois\n"
            progress_callback.emit(all_text)
    else:
        all_text = all_text + f"PA_Combined_Report.csv file not available, first run brand report\n"
        progress_callback.emit(all_text)
    return "Done."