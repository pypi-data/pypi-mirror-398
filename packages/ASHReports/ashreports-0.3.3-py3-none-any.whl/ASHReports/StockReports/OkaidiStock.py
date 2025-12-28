import polars as pl
import os
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.SaleAndStock import prepareStockDF
from ASHC_v3.Masters import OKMerchHier

def startOkaidiStockReportWorker(mw, progress_callback):
        all_text = ""
        inputFile = os.path.join(mw.output_folder,"Combined","OK_Combined_Report.csv")
        stockSeasonFilter = ["22H","23E","23H","24E","24H","25E","25H","26E","26H","27E","27H","NOS"]
        # Get all user inputs
        saleFileDir = mw.saleReportPath_lineedit.text()
        stockFileDir = mw.stockReportPath_lineedit.text()
        masterFileDir = mw.masterFolderPath_lineedit.text()
        dataFileDir = mw.dataFolderPath_lineedit.text()
        # Initiate Class parameters
        initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
        all_text = all_text + "Okaidi Stock Report Process Started\n"
        progress_callback.emit(all_text)
        # define file patterns
        stockFilePath = os.path.join(stockFileDir,'OK_*.csv.gz')
        df_stk = pl.scan_csv(stockFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
        ok_Pvt = df_stk.filter(pl.col('Season Code').is_in(stockSeasonFilter))
        pl_PvtStkOK = OKMerchHier(ok_Pvt)
        AllStock = prepareStockDF(pl_PvtStkOK)
        AllStockOK = AllStock.filter(pl.col('Brand Code') == 'OK')
        AllStockOK = AllStockOK.with_columns(pl.col("Division").map_elements(lambda x: x if ((x == "Okaidi") or (x == "Obaibi")) else "Okaidi", return_dtype=pl.String).alias('Division'),)
        AllStockOK = AllStockOK.with_columns(pl.col("Product Group").cast(pl.String).str.strip_chars())
        AllStockOK = AllStockOK.with_columns(pl.col("Product Group").map_elements(lambda x: x if ((x == "Fille") or (x == "Garcon")  or (x == "Mixte")) else "Garcon", return_dtype=pl.String).alias('Product Group'),)
        AllStockOK = AllStockOK.with_columns(pl.col("Item Category").map_elements(lambda x: "Clothing" if str(x)=="0" else x, return_dtype=pl.String).alias('Item Category'),)
        AllStockOK = AllStockOK.with_columns((AllStockOK['Division'] + AllStockOK['Product Group'] + AllStockOK['Item Category']).alias('Department'),)
        AllStockOK = AllStockOK.with_columns(pl.col("Style Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Style Code'),)
        AllStockOK = AllStockOK.with_columns(pl.col("Colour Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Colour Code'),)
        AllStockOK = AllStockOK.with_columns((pl.col('Style Code') + pl.col('Colour Code')).alias('RefCode'),)
        pl_Pvt = AllStockOK[["Country","Location Code","ShortName","Location Type","RefCode","Item No_","Style Code","Colour Code","Size","Department","Item Class","Remarks","Season Code","Unit Price","Current Retail Price","Closing Stock","Unit Cost"]]
        pl_Pvt.write_csv(os.path.join(mw.output_folder,f"OK_Filtered_Season_Stock_Report.csv"), separator=",")

        cdf = pl.read_csv(inputFile)
        cdf = cdf.filter(pl.col("Season Code").is_in(stockSeasonFilter))
        cdf = cdf.with_columns((cdf['Cumm. SaleValue'] + cdf['MTD SaleValue'] + cdf['WTD SaleValue'] + cdf['StockRetail'] + cdf['StockOrgRetail']).alias('ZeroFilter'))
        cdf = cdf.filter(pl.col('ZeroFilter').ne(0))
        cdf = cdf.with_columns((cdf['Division'] + pl.lit(" - ") + cdf['Product Group'] + pl.lit(" - ") + cdf['Item Category']).alias('Dept'))
        cdf.write_csv(os.path.join(mw.output_folder,f"OK_FilteredStockReport.csv"), separator=",")

        all_text = all_text + "Okaidi Stock Report Process Ended\n"
        progress_callback.emit(all_text)
        return "Done."

    