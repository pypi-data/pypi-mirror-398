import os
import polars as pl
from datetime import datetime
import datetime as dt
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.CommonFunction import dictMerge, fnCurrencyConverter, MapOffer, fnAgeMap, changeFWSeason
from ASHC_v3.SaleAndStock import cummelativeSale, removeWarehouseSale, prepareSaleDF, prepareStockDF, prepareBudgetFiles, prepareKPIFiles
from ASHC_v3.DateFunctions import makeDateIndex, makeDateRangeDict, makeMTD_YTDIndex, makeSaleSeasonDict, makeSaleSeasonIndex
from ASHC_v3.SaleAndStockExtra import calculateFCCost, returnFirstAndLastPurchDate, returnUnitCost

def PP1(mw, bname, pl_SaleDF, pl_StkDF):
    all_text = ""
    weekly_report_cols = ['Division','Product Group','Item Category','Age_Group','YTD','WTD','Item Class','Item Sub Class','Sub Class','Theme','Type','Remarks']

    SaleSummary_Idx = ["Country","City","Location Code","StoreName","ShortName","Location Type","LFL Status","Comp","Year","Quarter","Month","MerchWeek",
                       "Posting Date","Brand Code","Season Code","Sale_Period","Season_Group","Division","Product Group","Item Category","Item Class",
                       "Item Sub Class","Sub Class","Theme","Remarks","Disc_Status","OfferDetail","StoreSize","Age_Group","YTD","WTD"]
    
    StyleSummary_Idx = ["Country","City","Location Code","StoreName","ShortName","Location Type","LFL Status","Comp","Year","Quarter","Month","MerchWeek",
                        "Posting Date","Brand Code","Style Code","Colour Code","Season Code","Sale_Period","Season_Group","Division","Product Group",
                        "Item Category","Item Class","Item Sub Class","Sub Class","Theme","Remarks","Disc_Status","OfferDetail","First Purchase Date",
                        "Last Receive Date","StoreSize","Age(Days)","Age_Group","YTD","WTD","Unit_Cost","Unit_Price","Current_Price"]
    
    pVal = ["Visitors","Buyers","Target Amount","Total Purchase Qty","Closing Stock","Total Stock Cost(AED)","Total Stock Retail(AED)","SaleQty",
            "Total Sale Cost(AED)","Total Sale Retail(AED)","Total Sale Org. Retail(AED)","Discount Value","GrossMargin Value","FC Cost (AED)"]
    
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    pl_SaleDF = removeWarehouseSale(pl_SaleDF)
    ytdStart = mw.ytdStart_dateedit.date()
    yearTodateStart = ytdStart.toPython()
    ytdEnd = mw.ytdEnd_dateedit.date()
    yearTodateEnd = ytdEnd.toPython()
    wtdStart = mw.wtdStart_dateedit.date()
    weekTodateStart = wtdStart.toPython()
    wtdEnd = mw.wtdEnd_dateedit.date()
    weekTodateEnd = wtdEnd.toPython()
    lywtdStart = mw.lywtdStart_dateedit.date()
    lyweekTodateStart = lywtdStart.toPython()
    lywtdEnd = mw.lywtdEnd_dateedit.date()
    lyweekTodateEnd = lywtdEnd.toPython()
    ucs, ups, ucp = returnUnitCost()
    dictFRD, dictLRD = returnFirstAndLastPurchDate()

    ytd_NoOfDays = yearTodateStart - yearTodateEnd
    ytdDays = ytd_NoOfDays.days
    allSesDict = makeSaleSeasonDict()
    yearDateDict = makeMTD_YTDIndex(str(yearTodateStart), str(yearTodateEnd),"YTD")
    tyWeekDateDict = makeSaleSeasonIndex(str(weekTodateStart), str(weekTodateEnd),"WTD")
    lyWeekDateDict = makeSaleSeasonIndex(str(lyweekTodateStart), str(lyweekTodateEnd),"WTD")
    weekDateDict = dictMerge(tyWeekDateDict, lyWeekDateDict)
    ytdDateDict = makeDateRangeDict(str(yearTodateStart), str(yearTodateEnd))
    weekDateDictLY = makeDateIndex(str(lyweekTodateStart), str(lyweekTodateEnd))
    selectionDict = dictMerge(ytdDateDict, weekDateDictLY)
    budgetDF = prepareBudgetFiles(selectionDict)
    kpiDF = prepareKPIFiles(selectionDict)

    AllSale = prepareSaleDF(pl_SaleDF)
    #dfCummSale  = cummelativeSale(AllSale)
    AllSale = AllSale.with_columns(pl.col("Posting Date").replace_strict(selectionDict, default=None).alias('Copy_Date'))
    AllSale = AllSale.filter(pl.col('Copy_Date') == 1)
    df_AllSaleOK = AllSale.filter(pl.col('Brand Code') == 'OK')
    df_AllSaleOT = AllSale.filter(pl.col('Brand Code').is_in(['JC','PA','UZ','VI','YR','LS']))
    df_AllSaleOK = df_AllSaleOK.with_columns(pl.col("Division").map_elements(lambda x: x if ((x == "Okaidi") or (x == "Obaibi")) else "Okaidi", return_dtype=pl.String).alias('Division'),)
    df_AllSaleOK = df_AllSaleOK.with_columns(pl.col("Product Group").cast(pl.String).str.strip_chars())
    df_AllSaleOK = df_AllSaleOK.with_columns(pl.col("Product Group").map_elements(lambda x: x if ((x == "Fille") or (x == "Garcon")  or (x == "Mixte")) else "Garcon", return_dtype=pl.String).alias('Product Group'),)
    df_AllSaleOK = df_AllSaleOK.with_columns(pl.col("Item Category").map_elements(lambda x: "Clothing" if str(x)=="0" else x, return_dtype=pl.String).alias('Item Category'),)
    df_AllSaleF01 = pl.concat([df_AllSaleOK,df_AllSaleOT], how="diagonal")
    df_AllSaleF01 = df_AllSaleF01.fill_null(0)
    df_AllSale = df_AllSaleF01.fill_nan(0)

    fcCost = calculateFCCost(df_AllSale, ytdDays)
    df_AllKPIS = pl.concat([fcCost,budgetDF,kpiDF], how="diagonal")
    AllStock = prepareStockDF(pl_StkDF)
    AllStockOK = AllStock.filter(pl.col('Brand Code') == 'OK')
    AllStockOT = AllStock.filter(pl.col('Brand Code').is_in(['JC','PA','UZ','VI','YR','LS']))
    AllStockOK = AllStockOK.with_columns(pl.col("Division").map_elements(lambda x: x if ((x == "Okaidi") or (x == "Obaibi")) else "Okaidi", return_dtype=pl.String).alias('Division'),)
    AllStockOK = AllStockOK.with_columns(pl.col("Product Group").cast(pl.String).str.strip_chars())
    AllStockOK = AllStockOK.with_columns(pl.col("Product Group").map_elements(lambda x: x if ((x == "Fille") or (x == "Garcon")  or (x == "Mixte")) else "Garcon", return_dtype=pl.String).alias('Product Group'),)
    AllStockOK = AllStockOK.with_columns(pl.col("Item Category").map_elements(lambda x: "Clothing" if str(x)=="0" else x, return_dtype=pl.String).alias('Item Category'),)
    AllStock00 = pl.concat([AllStockOK,AllStockOT], how="diagonal").fill_null(0).fill_nan(0)
    #df_SaleAndStock = pl.concat([df_AllSale, dfCummSale, AllStock00], how="diagonal")
    df_SaleAndStock = pl.concat([df_AllSale, AllStock00], how="diagonal")
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.col("Location Code").replace_strict(mw.deleteStoreDisct, default=None).alias('Remove_Location'))
    df_SaleAndStock = df_SaleAndStock.filter(pl.col('Remove_Location').is_null()).fill_null(0).fill_nan(0)
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.when(pl.col('Season Code').is_in(ashc.selectSeason)).then(df_SaleAndStock['Season Code']).otherwise(pl.lit("OSM")).alias('Season_Group'))
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.col("Season_Group").map_elements(changeFWSeason, return_dtype=pl.String).alias('Season_Group'),)
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.col("Posting Date").replace_strict(allSesDict, return_dtype=pl.String, default=None).alias('Sale_Period'))
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.col("Location Code").replace_strict(ashc.City, return_dtype=pl.String, default=None).alias('City'))
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.col("Location Code").replace_strict(ashc.Country, return_dtype=pl.String, default=None).alias('Country'))
    df_SaleAndStock = df_SaleAndStock.filter(pl.col('Brand Code').is_in(mw.brandList))
    df_SaleAndStock = df_SaleAndStock.with_columns((abs(pl.col('SaleQty')) + abs(pl.col('Closing Stock'))).alias('ZeroFilter'),)
    df_SaleAndStock = df_SaleAndStock.filter(pl.col('ZeroFilter') > 0)
    df_SaleAndStock = df_SaleAndStock.with_columns((df_SaleAndStock['Location Code'] + df_SaleAndStock['Item No_']).alias('Combo'))
    df_SaleAndStock = df_SaleAndStock.with_columns((df_SaleAndStock['Discount Value'] / df_SaleAndStock['Total Sale Org. Retail(AED)']).alias('Disc.P'))
    df_SaleAndStock = df_SaleAndStock.with_columns(pl.when(df_SaleAndStock['Disc.P'] > 0.10).then(pl.lit("Discounted")).otherwise(pl.lit("Non Discounted")).alias('Disc_Status'))
    df_SaleAndStock = MapOffer(df_SaleAndStock)
    df_tmpKPI = df_AllKPIS.filter(pl.col('Brand Code') == bname)
    df_br = pl.concat([df_tmpKPI,df_SaleAndStock], how="diagonal").fill_null(0).fill_nan(0)
    df_SaleAndStockPVT = df_br.with_columns(pl.col("Style Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Style Code'),)

    if bname == "OK" or bname == "JC":
        df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Colour Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Colour Code'),)
    else:
        df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Colour Code").cast(pl.String).str.replace_all('.0','',literal=True).alias('Colour Code'),)

    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Combo").replace_strict(ucs, return_dtype=pl.Float32, default=None).alias('Unit_Cost'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Combo").replace_strict(ups, return_dtype=pl.Float32, default=None).alias('Unit_Price'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Combo").replace_strict(ucp, return_dtype=pl.Float32, default=None).alias('Current_Price'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns((pl.col("Location Code") + pl.col("MerchWeek")).alias('Combox'),)
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Combox").replace_strict(ashc.Lfl, return_dtype=pl.String, default=None).alias('LFL Status'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns((df_SaleAndStockPVT['SaleQty'] + df_SaleAndStockPVT['Closing Stock']).alias('Total Purchase Qty'),)
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Combo").replace_strict(dictFRD, default=None).alias('First Purchase Date'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Combo").replace_strict(dictLRD, default=None).alias('Last Receive Date'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Location Code").replace_strict(ashc.Area, return_dtype=pl.Float32, default=None).alias('StoreSize'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.lit(dt.datetime.today()).alias('Date(Today)'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.when(df_SaleAndStockPVT['First Purchase Date'].is_null()).then(df_SaleAndStockPVT['Date(Today)']).otherwise(df_SaleAndStockPVT['First Purchase Date']).alias('First Purchase Date'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(((df_SaleAndStockPVT['Date(Today)'] - df_SaleAndStockPVT['Last Receive Date']).dt.total_days()).alias('A01'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(((df_SaleAndStockPVT['Date(Today)'] - df_SaleAndStockPVT['First Purchase Date']).dt.total_days()).alias('A02'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.when(df_SaleAndStockPVT['A02'] > 0).then(df_SaleAndStockPVT['A02']).otherwise(df_SaleAndStockPVT['A01']).alias('Age(Days)'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Age(Days)").map_elements(fnAgeMap, return_dtype=pl.String).alias('Age_Group'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Posting Date").replace_strict(yearDateDict, default=None).alias('YTD'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Posting Date").replace_strict(weekDateDict, default=None).alias('WTD'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.when(pl.col('Season Code').is_in(ashc.selectSeason)).then(df_SaleAndStockPVT['Season Code']).otherwise(pl.lit("OSM")).alias('Season_Group'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Season_Group").map_elements(changeFWSeason, return_dtype=pl.String).alias('Season_Group'),)
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Posting Date").replace_strict(allSesDict, return_dtype=pl.String, default=None).alias('Sale_Period'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Location Code").replace_strict(ashc.City, return_dtype=pl.String, default=None).alias('City'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col("Location Code").replace_strict(ashc.Country, return_dtype=pl.String, default=None).alias('Country'))
    #df_SaleAndStockPVT.write_csv(os.path.join(mw.output_folder,"ItemSummary",f"{bname}_DetailSaleAndStock.csv"), separator=",")
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col('LFL Status').fill_null('NonLFL'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col('Sale_Period').fill_null('All'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col('OfferDetail').fill_null('Not in Offer'))
    df_SaleAndStockPVT = df_SaleAndStockPVT.with_columns(pl.col(weekly_report_cols).fill_null('NA'))
    df_Final = df_SaleAndStockPVT.group_by(StyleSummary_Idx).agg(pl.sum(pVal),).fill_null(0).fill_nan(0)
    all_text = all_text + f"Started saving {bname}_AllMerged.csv...\n"
    df_Final.write_csv(os.path.join(mw.output_folder,"StyleSummary",f"{bname}_AllMerged.csv"))

    df_FinalSummary = df_SaleAndStockPVT.group_by(SaleSummary_Idx).agg(pl.sum(pVal),)
    df_FinalSummary = df_FinalSummary.fill_null(0)
    df_FinalSummary = df_FinalSummary.fill_nan(0)
    df_FinalSummary = df_FinalSummary.with_columns(pl.lit('All').alias('Company'),)
    all_text = all_text + f"Started saving {bname}_AllMergedSummary.csv...\n"
    df_FinalSummary.write_csv(os.path.join(mw.output_folder,"SaleSummary",f"{bname}_AllMergedSummary.csv"))
    return "Done"


def PP2(mw, saleFileDir, stockFileDir, bname, ucs, ups, ucp, dictFRD, dictLRD):
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    ytdStart = mw.ytdStart_dateedit.date()
    yearTodateStart = ytdStart.toPython()
    ytdEnd = mw.ytdEnd_dateedit.date()
    yearTodateEnd = ytdEnd.toPython()
    mtdStart = mw.mtdStart_dateedit.date()
    monthTodateStart = mtdStart.toPython()
    mtdEnd = mw.mtdEnd_dateedit.date()
    monthTodateEnd = mtdEnd.toPython()
    wtdStart = mw.wtdStart_dateedit.date()
    weekTodateStart = wtdStart.toPython()
    wtdEnd = mw.wtdEnd_dateedit.date()
    weekTodateEnd = wtdEnd.toPython()
    if bname == "All":
        saleFilePath = os.path.join(saleFileDir, '*.csv.gz')
        stockFilePath = os.path.join(stockFileDir, '*.csv.gz')
    else:
        saleFilePath = os.path.join(saleFileDir, bname + '*.csv.gz')
        stockFilePath = os.path.join(stockFileDir, bname + '*.csv.gz')

    df = pl.scan_csv(saleFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    df01 = removeWarehouseSale(df)
    df01 = df01[["Posting Date","Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","SaleQty","CostValue","SaleValue"]]
    df_CummSaleTY = df01.filter(pl.col("Posting Date").is_between(yearTodateStart, yearTodateEnd))
    df_CummSaleTY = df_CummSaleTY.rename({'SaleQty':'Cumm. SaleQty','CostValue':'Cumm. CostValue','SaleValue':'Cumm. SaleValue'})
    df_CummSaleTY = df_CummSaleTY[["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","Cumm. SaleQty","Cumm. CostValue","Cumm. SaleValue"]]
    df_MTDSaleTY = df01.filter(pl.col("Posting Date").is_between(monthTodateStart, monthTodateEnd))
    df_MTDSaleTY = df_MTDSaleTY.rename({'SaleQty':'MTD SaleQty','CostValue':'MTD CostValue','SaleValue':'MTD SaleValue'})
    df_MTDSaleTY = df_MTDSaleTY[["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","MTD SaleQty","MTD CostValue","MTD SaleValue"]]
    df_WTDSaleTY = df01.filter(pl.col("Posting Date").is_between(weekTodateStart, weekTodateEnd))
    df_WTDSaleTY = df_WTDSaleTY.rename({'SaleQty':'WTD SaleQty','CostValue':'WTD CostValue','SaleValue':'WTD SaleValue'})
    df_WTDSaleTY = df_WTDSaleTY[["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","WTD SaleQty","WTD CostValue","WTD SaleValue"]]
    df_stk = pl.scan_csv(stockFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    df_stk = df_stk[["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code","Closing Stock","Unit Cost","Unit Price","Current Retail Price"]]
    df_stk = df_stk.with_columns((df_stk['Closing Stock'] * df_stk['Unit Cost']).alias('StockCost'),)
    df_stk = df_stk.with_columns((df_stk['Closing Stock'] * df_stk['Unit Price']).alias('StockOrgRetail'),)
    df_stk = df_stk.with_columns((df_stk['Closing Stock'] * df_stk['Current Retail Price']).alias('StockRetail'),)
    df_saleandstock = pl.concat([df_CummSaleTY,df_MTDSaleTY,df_WTDSaleTY,df_stk], how="diagonal")
    pIdx = ["Location Code","StoreName","Brand Code","Style Code","Description","Colour Code","Size","Item No_","Season Code"]
    df_SaleAndStock01 = df_saleandstock.group_by(pIdx).agg(pl.sum(['Cumm. SaleQty','MTD SaleQty','WTD SaleQty','Cumm. CostValue','MTD CostValue','WTD CostValue','Cumm. SaleValue','MTD SaleValue','WTD SaleValue','Closing Stock','StockCost','StockOrgRetail','StockRetail']),)
    df_SaleAndStock01 = df_SaleAndStock01.with_columns((df_SaleAndStock01['Location Code'] + df_SaleAndStock01['Item No_']).alias('Combo'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Combo").replace_strict(dictFRD, return_dtype=pl.Datetime, default=None).alias('First Purchase Date'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Combo").replace_strict(dictLRD, return_dtype=pl.Datetime, default=None).alias('Last Receive Date'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Location Code").replace_strict(ashc.Country, return_dtype=pl.String, default=None).alias('Country'))
    df_SaleAndStock01 = df_SaleAndStock01.with_columns(pl.col("Location Code").replace_strict(ashc.City, return_dtype=pl.String, default=None).alias('City'))
    pl_Pvt01 = df_SaleAndStock01[['Location Code','Item No_','Closing Stock','First Purchase Date','Last Receive Date','StoreName','Brand Code','Style Code','Colour Code','Size','Description','Country','City','Season Code','StockCost','StockRetail','StockOrgRetail','Cumm. SaleQty','Cumm. CostValue','Cumm. SaleValue','MTD SaleQty','MTD CostValue','MTD SaleValue','WTD SaleQty','WTD CostValue','WTD SaleValue']]
    pl_Pvt01 = pl_Pvt01.with_columns((pl_Pvt01['Location Code'] + pl_Pvt01['Item No_']).alias('Combo'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Combo").replace_strict(ucs, return_dtype=pl.Float64, default=None).alias('Unit Cost'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Combo").replace_strict(ups, return_dtype=pl.Float64, default=None).alias('Unit Price'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Combo").replace_strict(ucp, return_dtype=pl.Float64, default=None).alias('Current Price'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.lit(datetime.today()).alias('Date(Today)'),)
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Location Code").replace_strict(ashc.ShortStoreName, return_dtype=pl.String, default=None).alias('ShortName'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Location Code").replace_strict(ashc.LocationType, return_dtype=pl.String, default=None).alias('Location Type'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Location Code").replace_strict(ashc.Area, return_dtype=pl.Float64, default=None).alias('StoreSize'))
    pl_Pvt01 = pl_Pvt01.with_columns(pl.col("Country").map_elements(fnCurrencyConverter, return_dtype=pl.Float64).alias('ExchangeRate(AED)'),)
    df_SaleAndStock01 = pl_Pvt01.with_columns((abs(pl.col('Cumm. SaleQty')) + abs(pl.col('MTD SaleQty')) + abs(pl.col('Closing Stock'))).alias('ZeroFilter'),)
    pl_Pvt = df_SaleAndStock01.filter(pl.col('Brand Code') == bname)
    return pl_Pvt