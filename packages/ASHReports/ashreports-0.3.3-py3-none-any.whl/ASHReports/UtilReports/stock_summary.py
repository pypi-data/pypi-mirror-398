import os
import polars as pl
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig

def StockDump(mw, progress_callback):
    all_text = ""
    all_text = all_text + "Starting Stock Dump Report Process\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Starting Stock Dump Report Process")
    
    exch_rate = {"AE":1.00000,"BH":9.74143,"OM":9.53929,"QA":1.00878,"KWT":12.00000}
    monthDict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)

    df = pl.scan_csv(stockFileDir,schema_overrides=ashc.dataTypeForAll,).fill_null(0).collect()
    df = df.fill_nan(0)
    df = df.with_columns(pl.col('Country').replace_strict(exch_rate, default=None).alias('ExchRate'))
    df = df.with_columns(pl.col('Posting Date').dt.year().alias('Year'))
    df = df.with_columns(pl.col('Posting Date').dt.month().alias('tmpMonth'))
    df = df.with_columns(pl.col('tmpMonth').replace_strict(monthDict, default=None).alias('Month'))
    df = df.with_columns(pl.col('Posting Date').dt.week().alias('Week'))
    df = df.with_columns('WK' + pl.col("Week").cast(pl.String).alias('Week'))
    df = df.with_columns(pl.col("Posting Date").replace_strict(ashc.Week_, return_dtype=pl.String, default=None).alias('MerchWeek'))
    df = df.with_columns(pl.col("Location Code").replace_strict(ashc.ShortStoreName, return_dtype=pl.String, default=None).alias('ShortName'))
    df = df.with_columns(pl.col('Location Code').replace_strict(ashc.LocationType, return_dtype=pl.String, default=None).alias('Location Type'))
    df = df.with_columns((pl.col('Closing Stock') * pl.col('Unit Cost') * pl.col('ExchRate')).alias('Stk Cost (AED)'))
    df = df.with_columns((pl.col('Closing Stock') * pl.col('Current Retail Price') * pl.col('ExchRate')).alias('Stk Retail(AED)'))
    df = df.with_columns((pl.col('Closing Stock') * pl.col('Unit Price') * pl.col('ExchRate')).alias('Stk OrgAmt(AED)'))
    print(df.shape)
    df01 = df[['Year','Month','MerchWeek','Country','Location Code','ShortName','Location Type','Brand Code','Item No_','Style Code','Colour Code','Size','Season Code','Unit Price','Closing Stock','Stk Cost (AED)','Stk Retail(AED)','Stk OrgAmt(AED)']]
    wek = df01.select('MerchWeek').unique()[0]
    weks = pl.Series(wek.select('MerchWeek')).to_list()
    fname = f"{weks[0]}-stock.csv"
    df01.write_csv(os.path.join(mw.output_folder,fname), separator=",")
    all_text = all_text + f"Stock Dump Report Completed\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Stock Dump Report Completed")
    return "Done"
