import polars as pl
import os,datetime
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.DateFunctions import makeDateIndex, makeDateRangeDict, makeMTD_YTDIndex, makeSaleSeasonIndex
from ASHC_v3.CommonFunction import dictMerge
from ASHC_v3.SaleAndStock import prepareKPIFiles, prepareSaleDF, removeWarehouseSale

def startWeeklyReportWorker(mw, progress_callback):
    extract_columns = ['Date','Type','Company Name','Country','Brand Code','Department','Profit Centre Code','Location Name','Store Opening Date','Store Size','Date Day Description','I Ns','OU Ts','Quantity','Sales Amount LCY','Sales Amount BASE','Target Amount BASE','Amount Tendered BASE']
    DE_saleFiles = "C:\\Reports\\Data\\a21\\2.1a_*.csv.gz"
    brand = "DE"
    all_text = ""
    all_text = all_text + f"Weekly Report Process Started for {brand}...\n"
    progress_callback.emit(all_text)

    current_dateTime = datetime.datetime.now()
    todayDate = f"{current_dateTime.year}-{current_dateTime.month}-{current_dateTime.day}"
    
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
    wtdStart = mw.wtdStart_dateedit.date()
    weekTodateStart = wtdStart.toPython()
    wtdEnd = mw.wtdEnd_dateedit.date()
    weekTodateEnd = wtdEnd.toPython()
    lywtdStart = mw.lywtdStart_dateedit.date()
    lyweekTodateStart = lywtdStart.toPython()
    lywtdEnd = mw.lywtdEnd_dateedit.date()
    lyweekTodateEnd = lywtdEnd.toPython()
    
    sesDateDict = makeMTD_YTDIndex(str(yearTodateStart), str(yearTodateEnd),"STD")
    yearDateDict = makeMTD_YTDIndex(str(yearTodateStart), str(yearTodateEnd),"YTD")
    monthDateDict = makeMTD_YTDIndex(str(yearTodateStart), str(yearTodateEnd),"MTD")
    tyWeekDateDict = makeSaleSeasonIndex(str(yearTodateStart), str(yearTodateEnd),"WTD")
    lyWeekDateDict = makeSaleSeasonIndex(str(lyweekTodateStart), str(lyweekTodateEnd),"WTD")
    weekDateDict = dictMerge(tyWeekDateDict, lyWeekDateDict)

    sesSelectionDict = makeDateRangeDict(str(yearTodateStart), str(yearTodateEnd))
    weekDateDictLY = makeDateIndex(str(lyweekTodateStart), str(lyweekTodateEnd))
    selectionDict = dictMerge(sesSelectionDict, weekDateDictLY)

    df = pl.scan_csv(DE_saleFiles,).fill_null(0).fill_nan(0).collect()

    df = df.with_columns(pl.col('Date').str.to_datetime(format='%d/%m/%Y').alias('Date'))
    df01 = df[extract_columns]
    df01 = df01.rename({'Date':'Posting Date','Department':'Division','Profit Centre Code':'Location Code','Location Name':'StoreName','Quantity':'SaleQty','Sales Amount LCY':'SaleValue'})
    df01 = df01.with_columns(pl.col("Location Code").map_elements(lambda x: str(x).replace(".0","")[-4:], return_dtype=pl.String).alias('Location Code'),)
    pvt_index=['Posting Date','Company Name','Country','Brand Code','Division','Location Code','StoreName']
    pvt_values=['SaleQty','SaleValue','Sales Amount BASE','Target Amount BASE','Amount Tendered BASE']
    df01 = df01.group_by(pvt_index).agg(pl.sum(pvt_values)).fill_null(0).fill_nan(0)

    df01 = df01.with_columns(pl.lit("NA").alias('Season Code'),)
    df01 = df01.with_columns(pl.lit("111").alias('Style Code'),)
    df01 = df01.with_columns(pl.lit("111").alias('Colour Code'),)
    df01 = df01.with_columns(pl.lit("NA").alias('Size'),)
    df01 = df01.with_columns(pl.lit(0.0).alias('CostValue'),)
    df01 = df01.with_columns(pl.lit('111111').alias('Item No_'),)

    df01 = df01.with_columns((df01['SaleValue'] / df01['SaleQty']).alias('Unit Price Including VAT'))
    df02 = removeWarehouseSale(df01)
    df03 = prepareSaleDF(df02)
    df03 = df03.rename({'Target Amount BASE':'Target Amount'})
    df03 = df03.with_columns(pl.lit('FW25').alias('Season Code'),)
    df03 = df03.with_columns(pl.lit('FW25').alias('Sale_Season'),)
    df03 = df03.with_columns(pl.lit('FW25').alias('Season_Group'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Product Group'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Item Category'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Item Class'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Item Sub Class'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Sub Class'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Theme'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Remarks'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Disc_Status'),)
    df03 = df03.with_columns(pl.lit('NA').alias('OfferDetail'),)
    df03 = df03.with_columns(pl.lit('1900-01-01').alias('First Purchase Date'),)
    df03 = df03.with_columns(pl.lit('1900-01-01').alias('Last Receive Date'),)
    df03 = df03.with_columns(pl.col('First Purchase Date').str.to_datetime().alias('First Purchase Date'))
    df03 = df03.with_columns(pl.col('Last Receive Date').str.to_datetime().alias('Last Receive Date'))
    df03 = df03.with_columns(pl.lit(0).alias('Age(Days)'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Season2'),)
    df03 = df03.with_columns(pl.lit('NA').alias('Age_Group'),)
    df03 = df03.with_columns(pl.lit(0.0, dtype=pl.Float32).alias('Unit_Cost'),)
    df03 = df03.with_columns(pl.lit(0.0, dtype=pl.Float32).alias('Unit_Price'),)
    df03 = df03.with_columns(pl.lit(0.0, dtype=pl.Float32).alias('Current_Price'),)
    df03 = df03.with_columns(pl.lit(0).alias('Total Purchase Qty'),)
    df03 = df03.with_columns(pl.lit(0).alias('Closing Stock'),)
    df03 = df03.with_columns(pl.lit(0.0).alias('Total Stock Cost(AED)'),)
    df03 = df03.with_columns(pl.lit(0.0).alias('Total Stock Retail(AED)'),)
    df03 = df03.with_columns(pl.lit(0.0).alias('FC Cost (AED)'),)

    df03 = df03.with_columns(pl.col("Posting Date").replace_strict(sesDateDict, default=None).alias('STD'))
    df03 = df03.with_columns(pl.col("Posting Date").replace_strict(yearDateDict, default=None).alias('YTD'))
    df03 = df03.with_columns(pl.col("Posting Date").replace_strict(monthDateDict, default=None).alias('MTD'))
    df03 = df03.with_columns(pl.col("Posting Date").replace_strict(weekDateDict, default=None).alias('WTD'))

    df_StoreKPI = prepareKPIFiles(selectionDict)
    df_DE = pl.concat([df03,df_StoreKPI], how="diagonal").fill_null(0).fill_nan(0)

    df_DE = df_DE.with_columns(pl.col("Posting Date").replace_strict(selectionDict, default=None).alias('Copy_Date'))
    df_DE = df_DE.filter(pl.col('Copy_Date') == 1)
    df_DE = df_DE.with_columns(pl.col("Comp").replace_strict({"TY24":1,"TY25":1}, default=None).alias('Copy_TY'))
    df_DE = df_DE.filter(pl.col('Copy_TY') == 1)

    df_DE = df_DE.drop(['Copy_Date','Copy_TY'])
    df_DE = df_DE[["Posting Date","STD","YTD","MTD","WTD","Company Name","Country","Brand Code","Location Code","StoreName","SaleQty","SaleValue","Sales Amount BASE","Amount Tendered BASE","Style Code","Colour Code","Size","CostValue","Unit Price Including VAT","Total Sale Cost(AED)","Total Sale Retail(AED)","Unit Price Including VAT(AED)","ShortName","Location Type","StoreSize","MerchWeek","Year","Month","Quarter","Comp","Combox","LFL Status","ExchangeRate(AED)","Total Sale Org. Retail(AED)","GrossMargin Value","Discount Value","Discount Percent","Discount Status","Season Code","Sale_Season","Season_Group","Division","Product Group","Item Category","Item Class","Item Sub Class","Sub Class","Theme","Remarks","Disc_Status","OfferDetail","First Purchase Date","Last Receive Date","Age(Days)","Season2","Age_Group","Unit_Cost","Unit_Price","Current_Price","Total Purchase Qty","Closing Stock","Total Stock Cost(AED)","Total Stock Retail(AED)","FC Cost (AED)","City","Target Amount","Buyers","Visitors"]]

    p_index=["Posting Date","STD","YTD","MTD","WTD","Company Name","Country","Brand Code","Location Code","StoreName","City","Style Code","Colour Code","Size","ShortName","Location Type","MerchWeek","Year","Month","Quarter","Comp","LFL Status","Discount Status","Season Code","Sale_Season","Season_Group","Division","Product Group","Item Category","Item Class","Item Sub Class","Sub Class","Theme","Remarks","Disc_Status","OfferDetail"]
    p_values=["SaleQty","Total Sale Cost(AED)","Total Sale Retail(AED)","Total Sale Org. Retail(AED)","GrossMargin Value","Discount Value","Total Purchase Qty","Closing Stock","Total Stock Cost(AED)","Total Stock Retail(AED)","FC Cost (AED)","Target Amount","Buyers","Visitors"]

    df_DE01 = df_DE.group_by(p_index).agg(pl.sum(p_values)).fill_null(0).fill_nan(0)

    df_DE01 = df_DE01.with_columns(pl.col("Posting Date").replace_strict(sesDateDict, default=None).alias('STD'))
    df_DE01 = df_DE01.with_columns(pl.col("Posting Date").replace_strict(yearDateDict, default=None).alias('YTD'))
    df_DE01 = df_DE01.with_columns(pl.col("Posting Date").replace_strict(monthDateDict, default=None).alias('MTD'))
    df_DE01 = df_DE01.with_columns(pl.col("Posting Date").replace_strict(weekDateDict, default=None).alias('WTD'))

    file_name = f"2.1a_Summary_({todayDate}).csv"
    df_DE01.write_csv(os.path.join(mw.output_folder,file_name))

    df_DE01 = df_DE01.filter(pl.col('Brand Code').is_in(['DE']))
    df_DE01 = df_DE01.with_columns(pl.lit('NA').alias('Sale_Period'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0).alias('StoreSize'),)
    df_DE01 = df_DE01.with_columns(pl.lit('NA').alias('Age_Group'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0).alias('ST_Qty'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0.0).alias('ST_Cost(AED)'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0.0).alias('ST_Retail(AED)'),)
    df_DE01 = df_DE01[["Country","City","Location Code","StoreName","ShortName","Location Type","LFL Status","Comp","Year","Quarter","Month","MerchWeek","Posting Date","Brand Code","Season Code","Sale_Period","Season_Group","Division","Product Group","Item Category","Item Class","Item Sub Class","Sub Class","Theme","Remarks","Disc_Status","OfferDetail","StoreSize","Age_Group","YTD","WTD","Visitors","Buyers","Target Amount","Total Purchase Qty","Closing Stock","Total Stock Cost(AED)","Total Stock Retail(AED)","SaleQty","Total Sale Cost(AED)","Total Sale Retail(AED)","Total Sale Org. Retail(AED)","Discount Value","GrossMargin Value","FC Cost (AED)","ST_Qty","ST_Cost(AED)","ST_Retail(AED)"]]
    df_DE01 = df_DE01.with_columns(pl.lit('DE').alias('Company'),)
    df_DE01.write_csv(os.path.join(mw.output_folder,"SaleSummary","DE_AllMergedSummary.csv"))
    return "Done."