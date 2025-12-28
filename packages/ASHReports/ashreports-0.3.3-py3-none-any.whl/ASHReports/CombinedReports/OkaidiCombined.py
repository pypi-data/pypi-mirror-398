import os
import polars as pl
import ASHC_v3 as ashc
from ASHC_v3.Masters import OKMerchHier
from ASHC_v3.CommonFunction import MapOffer
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.SaleAndStockExtra import returnFirstAndLastPurchDate, returnUnitCost
from ASHReports.UtilReports.misc import PP2

def startCombinedReportWorker(mw, progress_callback):
    brand = "OK"
    all_text = ""
    all_text = all_text + f"Combined Report Process Started for {brand}...\n"
    progress_callback.emit(all_text)
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    ucs, ups, ucp = returnUnitCost()
    dictFRD, dictLRD = returnFirstAndLastPurchDate()
    pl_Pvt = PP2(mw, saleFileDir, stockFileDir, brand, ucs, ups, ucp, dictFRD, dictLRD)
    pl_Pvt = OKMerchHier(pl_Pvt)
    pl_Pvt = pl_Pvt.with_columns((pl_Pvt['Closing Stock'] + pl_Pvt['Cumm. SaleQty']).alias('Purchased'),)
    pl_Pvt = pl_Pvt.with_columns(pl.col("Location Code").replace_strict(ashc.Status, return_dtype=pl.String, default=None).alias('Status'))
    pl_Pvt = pl_Pvt.with_columns(pl.col("Style Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Style Code'),)
    try:
        pl_Pvt = pl_Pvt.with_columns(pl.col("Colour Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Colour Code'),)
    except:
        pl_Pvt = pl_Pvt.with_columns(pl.col("Colour Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Colour Code'),)
    
    pl_Pvt = pl_Pvt.with_columns((pl.col('Style Code') + pl.col('Colour Code')).alias('RefCode'),)
    pl_Pvt = pl_Pvt.with_columns((pl_Pvt['Country'] + pl_Pvt['RefCode']).alias('Combo2'),)
    pl_Pvt = pl_Pvt.with_columns(pl.lit(0.0,dtype=pl.Float32).alias('Disc.P'),)
    pl_Pvt = MapOffer(pl_Pvt)
    pl_Pvt = pl_Pvt.with_columns(pl.when(pl.col('Offer_Price') > 0.0).then(pl.lit('Disc')).otherwise(pl.lit(' ')).alias('EOSS Discount'),)
    pl_Pvt = pl_Pvt.with_columns(pl.when(pl.col('Offer_Price') > 0.0).then((pl.col('Unit Price') - pl.col('Offer_Price'))/pl.col('Unit Price')).otherwise(0).alias('Disc.P'),)
    
    #pl_Pvt = pl_Pvt.rename({'Season Code':'Season Item'})
    #pl_Pvt = pl_Pvt.rename({'Season':'Season Code'})
    pl_Pvt = pl_Pvt.filter(pl.col('Season Code').is_in(mw.currentSeason))
    #pl_Pvt = pl_Pvt.with_columns((pl_Pvt['Cumm. SaleQty'].abs() + pl_Pvt['Cumm. CostValue'].abs() + pl_Pvt['MTD SaleQty'].abs() + pl_Pvt['WTD SaleQty'].abs() + pl_Pvt['Closing Stock'].abs() + pl_Pvt['StockCost'].abs()).alias('ZeroFilter'),)
    #pl_Pvt = pl_Pvt.filter(pl.col('ZeroFilter')>0)
    
    pl_Pvt = pl_Pvt[mw.combined_report_columns]
    pl_Pvt.write_csv(os.path.join(mw.output_folder,"Combined",f"{brand}_Combined_Report.csv"), separator=",")
    s8 = pl_Pvt["Cumm. SaleQty"].sum()
    s9 = pl_Pvt["Closing Stock"].sum()
    all_text = all_text + f"OK Report Done, Cumm Sale Qty {s8} Closing Stock {s9}\n"
    progress_callback.emit(all_text)
    return "Done."