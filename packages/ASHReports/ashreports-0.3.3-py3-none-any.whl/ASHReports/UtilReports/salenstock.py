import os
import polars as pl
from datetime import datetime
import datetime as dt
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.SaleAndStockExtra import returnFirstAndLastPurchDate, returnUnitCost
from ASHC_v3.SaleAndStock import cummelativeSale, removeWarehouseSale
from ASHC_v3.CommonFunction import dictMerge, fnCurrencyConverter
from ASHC_v3.Masters import JCMerchHier,OKMerchHier,PAMerchHier,VIMerchHier,UZMerchHier,YRMerchHier
from ASHReports.UtilReports.misc import PP2

def SaleAndStockReport(mw, progress_callback):
    all_text = f"SaleAndStockReport\n"
    progress_callback.emit(all_text)
    report_columns = ["Brand Code","Country","City","Location Code","StoreName","ShortName","StoreSize","Location Type","Status","Division","Product Group",
                    "Item Category","Item Class","Item Sub Class","Theme","RefCode","Style Code","First Purchase Date","Last Receive Date","Colour Code",
                    "Size","Item No_","Season Code","Unit Price","Current Price","Unit Cost","ExchangeRate(AED)","Cumm. SaleQty","Cumm. CostValue",
                    "Cumm. SaleValue","Closing Stock","StockCost","StockRetail","StockOrgRetail","Purchased","Remarks","Combo2","Disc.P"]

    mw.infotextmisc_lable.setText(r"Working....")
    stkAsOn = mw.miscStart_dateedit.date()
    dt01 = stkAsOn.toPython()
    stkPostDate = mw.miscEnd_dateedit.date()
    dt02 = stkPostDate.toPython()
    brname = mw.miscbrandSelect_combobox.currentText()
    
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    # reusing code from sellthru file to make combine1
    inputFile = os.path.join(mw.output_folder,"Combined","OK_Combined_Report.csv")
    okSellThruFile = os.path.join(mw.output_folder,"OK_Combined_Report1.csv")
    path_exists = os.path.isfile(inputFile)
    if path_exists:
        cdf = pl.read_csv(inputFile)
        cdf = cdf.filter(pl.col("Season Code").is_in(mw.currentSeason))
        cdf.write_csv(okSellThruFile, separator=",")
    else:
        print("OK_Combined_Report.csv file is not available")
        mw.infotextmisc_lable.setText(r"OK_Combined_Report.csv file is not available")
    #-------------------------------------------------------
    ucs, ups, ucp = returnUnitCost()
    dictFRD, dictLRD = returnFirstAndLastPurchDate()

    saleFilePath = os.path.join(saleFileDir, brname + '*.csv.gz')
    stockFilePath = os.path.join(stockFileDir, brname + '*.csv.gz')
    mw.infotextmisc_lable.setText(r"Working....")
    df = pl.scan_csv(saleFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    df01 = removeWarehouseSale(df)
    df01 = df01[["Posting Date","Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","SaleQty","CostValue","SaleValue"]]
    df_CummSaleTY = df01.filter(pl.col("Posting Date").is_between(dt01, dt02))
    df_CummSaleTY = df_CummSaleTY.rename({'SaleQty':'Cumm. SaleQty','CostValue':'Cumm. CostValue','SaleValue':'Cumm. SaleValue'})
    df_CummSaleTY = df_CummSaleTY[["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","Cumm. SaleQty","Cumm. CostValue","Cumm. SaleValue"]]
    
    df_stk = pl.scan_csv(stockFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    df_stk = df_stk[["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","Closing Stock","Unit Cost","Unit Price","Current Retail Price"]]
    df_stk = df_stk.with_columns((df_stk['Closing Stock'] * df_stk['Unit Cost']).alias('StockCost'),)
    df_stk = df_stk.with_columns((df_stk['Closing Stock'] * df_stk['Unit Price']).alias('StockOrgRetail'),)
    df_stk = df_stk.with_columns((df_stk['Closing Stock'] * df_stk['Current Retail Price']).alias('StockRetail'),)
    df_saleandstock = pl.concat([df_CummSaleTY,df_stk], how="diagonal")

    pIdx = ["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code"]
    df_SaleAndStock01 = df_saleandstock.group_by(pIdx).agg(pl.sum(['Cumm. SaleQty','Cumm. CostValue','Cumm. SaleValue','Closing Stock','StockCost','StockOrgRetail','StockRetail']),)
    df_SaleAndStock01 = df_SaleAndStock01.with_columns((df_SaleAndStock01['Location Code'] + df_SaleAndStock01['Item No_']).alias('Combo'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Combo").replace_strict(dictFRD, return_dtype=pl.Datetime, default=None).alias('First Purchase Date'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Combo").replace_strict(dictLRD, return_dtype=pl.Datetime, default=None).alias('Last Receive Date'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Location Code").replace_strict(ashc.Country, return_dtype=pl.String, default=None).alias('Country'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Location Code").replace_strict(ashc.City, return_dtype=pl.String, default=None).alias('City'))
    pl_Pvt01 = df_SaleAndStock01[['Location Code','Item No_','Closing Stock','First Purchase Date','Last Receive Date','StoreName','Brand Code','Style Code','Colour Code','Size','Description','Country','City','Season Code','StockCost','StockRetail','StockOrgRetail','Cumm. SaleQty','Cumm. CostValue','Cumm. SaleValue']]
    pl_Pvt01 = pl_Pvt01.with_columns((pl_Pvt01['Location Code'] + pl_Pvt01['Item No_']).alias('Combo'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Combo").replace_strict(ucs, return_dtype=pl.Float64, default=None).alias('Unit Cost'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Combo").replace_strict(ups, return_dtype=pl.Float64, default=None).alias('Unit Price'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Combo").replace_strict(ucp, return_dtype=pl.Float64, default=None).alias('Current Price'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.lit(datetime.today()).alias('Date(Today)'),)
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Location Code").replace_strict(ashc.ShortStoreName, return_dtype=pl.String, default=None).alias('ShortName'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Location Code").replace_strict(ashc.LocationType, return_dtype=pl.String, default=None).alias('Location Type'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Location Code").replace_strict(ashc.Area, return_dtype=pl.Float64, default=None).alias('StoreSize'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Country").map_elements(fnCurrencyConverter, return_dtype=pl.Float64).alias('ExchangeRate(AED)'),)
    df_SaleAndStock01 = pl_Pvt01.with_columns((abs(pl.col('Cumm. SaleQty')) + abs(pl.col('Closing Stock'))).alias('ZeroFilter'),)
    pl_Pvt = df_SaleAndStock01.filter(pl.col('Brand Code') == brname)
    
    if brname == "JC":
        pl_Pvt = JCMerchHier(pl_Pvt)
    elif brname == "OK":
        pl_Pvt = OKMerchHier(pl_Pvt)
    elif brname == "PA":
        pl_Pvt = PAMerchHier(pl_Pvt)
    elif brname == "VI":
        pl_Pvt = VIMerchHier(pl_Pvt)
    elif brname == "UZ":
        pl_Pvt = UZMerchHier(pl_Pvt)
    elif brname == "YR":
        pl_Pvt = YRMerchHier(pl_Pvt)
    else:
        pass

    pl_Pvt = pl_Pvt.with_columns((pl_Pvt['Closing Stock'] + pl_Pvt['Cumm. SaleQty']).alias('Purchased'),)
    pl_Pvt = pl_Pvt.with_columns(pl.col("Location Code").replace_strict(ashc.Status, return_dtype=pl.String, default=None).alias('Status'))
    try:
        pl_Pvt = pl_Pvt.with_columns(pl.col("Colour Code").map_elements(lambda x: str(int(float(x))).replace(".0",""), return_dtype=pl.String).alias('Colour Code'),)
        #pl_Pvt = pl_Pvt.with_columns(pl.col("Colour Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Colour Code'),)
    except:
        pl_Pvt = pl_Pvt.with_columns(pl.col("Colour Code").map_elements(lambda x: str(x).replace(".0",""), return_dtype=pl.String).alias('Colour Code'),)
    pl_Pvt = pl_Pvt.with_columns((pl.col('Style Code') + pl.col('Colour Code')).alias('RefCode'),)
    pl_Pvt = pl_Pvt.with_columns((pl_Pvt['Country'] + pl_Pvt['RefCode']).alias('Combo2'),)
    pl_Pvt = pl_Pvt.with_columns(pl.lit(0.0,dtype=pl.Float32).alias('Disc.P'),)
    #pl_Pvt = pl_Pvt.with_columns(pl.when(pl.col('Offer_Price') > 0.0).then(pl.lit('Disc')).otherwise(pl.lit(' ')).alias('EOSS Discount'),)
    #pl_Pvt = pl_Pvt.with_columns(pl.when(pl.col('Offer_Price') > 0.0).then((pl.col('Unit Price') - pl.col('Offer_Price'))/pl.col('Unit Price')).otherwise(0).alias('Disc.P'),)
    
    #pl_Pvt = pl_Pvt.rename({'Season Code':'Season Item'})
    #pl_Pvt = pl_Pvt.rename({'Season':'Season Code'})
    pl_Pvt = pl_Pvt.filter(pl.col('Season Code').is_in(mw.currentSeason))
    #pl_Pvt = pl_Pvt.with_columns((pl_Pvt['Cumm. SaleQty'].abs() + pl_Pvt['Cumm. CostValue'].abs() + pl_Pvt['MTD SaleQty'].abs() + pl_Pvt['WTD SaleQty'].abs() + pl_Pvt['Closing Stock'].abs() + pl_Pvt['StockCost'].abs()).alias('ZeroFilter'),)
    #pl_Pvt = pl_Pvt.filter(pl.col('ZeroFilter')>0)
    pl_Pvt = pl_Pvt[report_columns]
    pl_Pvt.write_csv(os.path.join(mw.output_folder,f"{brname}_SaleNStock_Report.csv"), separator=",")
    mw.infotextmisc_lable.setText(r"Done....")
    return "Done."


def StyleAndPriceReport(mw, progress_callback):
    all_text = f"StyleAndPriceReport\n"
    progress_callback.emit(all_text)
    brname = mw.miscbrandSelect_combobox.currentText()
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    mw.infotextmisc_lable.setText(r"Working....")
    stockFilePath = os.path.join(stockFileDir, brname + '*.csv.gz')
    df = pl.read_csv(stockFilePath,infer_schema_length=0,).fill_null(0)
    df = df.filter(pl.col('Country').ne(''))
    try:
        df = df.with_columns(pl.col('Style Code').cast(pl.Int64).alias('Style Code'))
        df = df.with_columns(pl.col('Colour Code').cast(pl.Int64).alias('Colour Code'))
    except:
        print("Style code is not number")
    
    df = df.with_columns(pl.col('Closing Stock').cast(pl.Float32).alias('Closing Stock'))
    df = df.with_columns((df['Country'].cast(pl.String) + df['Style Code'].cast(pl.String)).alias('Combo1'))
    df = df.with_columns((df['Country'].cast(pl.String) + df['Item No_'].cast(pl.String)).alias('Combo2'))
    df = df.with_columns((df['Style Code'].cast(pl.String) + df['Colour Code'].cast(pl.String)).alias('RefCode'))
    df = df.group_by(["Combo1","Combo2","Country","Item No_","Style Code","Colour Code","RefCode","Unit Price"]).agg(pl.sum("Closing Stock"),)
    df.write_csv(os.path.join(mw.output_folder,f"{brname}_StyleAndPrice.csv"))
    mw.infotextmisc_lable.setText(r"Done....")
    return "Done."

def StyleAndSeasonReport(mw, progress_callback):
    all_text = f"StyleAndSeasonReport\n"
    progress_callback.emit(all_text)
    brname = mw.miscbrandSelect_combobox.currentText()
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    mw.infotextmisc_lable.setText(r"Working....")
    stockFilePath = os.path.join(stockFileDir, brname + '*.csv.gz')
    df = pl.read_csv(stockFilePath,infer_schema_length=0,).fill_null(0)
    df = df.filter(pl.col('Country').ne(''))
    try:
        df = df.with_columns(pl.col('Style Code').cast(pl.Int64).alias('Style Code'))
        df = df.with_columns(pl.col('Colour Code').cast(pl.Int64).alias('Colour Code'))
    except:
        print("Style code is not number")
    
    df = df.with_columns(pl.col('Closing Stock').cast(pl.Float32).alias('Closing Stock'))
    df = df.with_columns((df['Country'].cast(pl.String) + df['Style Code'].cast(pl.String)).alias('Combo1'))
    df = df.with_columns((df['Country'].cast(pl.String) + df['Item No_'].cast(pl.String)).alias('Combo2'))
    df = df.with_columns((df['Style Code'].cast(pl.String) + df['Colour Code'].cast(pl.String)).alias('RefCode'))
    df = df.group_by(["Combo1","Combo2","Country","Item No_","Style Code","Colour Code","RefCode","Season Code"]).agg(pl.sum("Closing Stock"),)
    df.write_csv(os.path.join(mw.output_folder,f"{brname}_StyleAndSeason.csv"))
    mw.infotextmisc_lable.setText(r"Done....")
    return "Done."