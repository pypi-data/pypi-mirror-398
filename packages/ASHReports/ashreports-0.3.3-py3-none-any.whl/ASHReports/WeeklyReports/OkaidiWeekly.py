import os
import polars as pl
import ASHC_v3 as ashc
from ASHReports.UtilReports.misc import PP1
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.Masters import OKMerchHier


def startWeeklyReportWorker(mw, progress_callback):
    brand = "OK"
    all_text = ""
    all_text = all_text + f"Weekly Report Process Started for {brand}...\n"
    progress_callback.emit(all_text)
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    
    saleFilePath = os.path.join(saleFileDir, brand + '*.csv.gz')
    stockFilePath = os.path.join(stockFileDir, brand + '*.csv.gz')
    
    df_sls = pl.scan_csv(saleFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    df_stk = pl.scan_csv(stockFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    pl_Pvt = OKMerchHier(df_sls)
    pl_PvtStk = OKMerchHier(df_stk)
    PP1(mw, brand, pl_Pvt, pl_PvtStk)
    all_text = all_text + f"{brand} Closing Stock Qty {df_stk['Closing Stock'].sum()}\n"
    all_text = all_text + f"{brand} Sale Qty {df_sls['SaleQty'].sum()}\n"
    progress_callback.emit(all_text)
    return "Done."