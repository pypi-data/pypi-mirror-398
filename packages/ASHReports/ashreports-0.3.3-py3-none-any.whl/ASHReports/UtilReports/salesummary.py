import os
import polars as pl
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig
from ASHC_v3.SaleAndStock import removeWarehouseSale

def SaleSummary(mw, progress_callback):
    all_text = ""
    all_text = all_text + f"Sale Summary Report Process Started for all brands\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Sale Summary Report Process Started for all brands")
    exRate = {"AE":1.00000,"BH":9.74143,"OM":9.53929,"QA":1.00878,"KWT":12.00000}
    year = [2019,2020,2021,2022,2023,2024,2025,2026]
    monthDict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    delList = {"DE98":1,"A01JC99":1,"JC99":1,"A01JC-TR":1,"A05JC99":1,"A05JC-TR":1,"A01OK3PL":1,"A01OK99":1,"OK92":1,"OK98":1,"OK99":1,"OK99R":1,"OK99S":1,"A01OK-TR":1,"A02OK99":1,"OK00":1,"OK99T":1,"A06OK99":1,"INTRANSIT":1,"A05OK-TR":1,"OK90":1,"A03OK-TR":1,"A02OK-TR":1,"PA98":1,"PA99":1,"A01PA-TR":1,"PA01D":1,"PA06D":1,"PA09D":1,"PA11D":1,"PA12D":1,"PA15D":1,"PA16D":1,"PA23D":1,"PA24D":1,"PA25D":1,"PA26D":1,"PA27D":1,"PA29D":1,"PA31D":1,"PA99D":1,"PA99S":1,"A06PA-TR":1,"A05PA-TR":1,"PA92":1,"A03PA-TR":1,"UZ98":1,"UZ99":1,"A01UZ-TR":1,"UZ99D":1,"UZ99R":1,"UZ90":1,"A03UZ-TR":1,"VI98":1,"VI99":1,"A01VI-TR":1,"VI00":1,"VI99D":1,"VI99R":1,"A06VI-TR":1,"VI90":1,"A03VI-TR":1,"VI92":1,"VI93":1,"A02VI-TR":1,"YR89":1,"YR99":1,"A01YR-TR":1,"YR99D":1,"YR99M":1,"YR99R":1,"PA90":1,"OK89":1}
    # Get all user inputs
    saleFileDir = mw.saleReportPath_lineedit.text()
    stockFileDir = mw.stockReportPath_lineedit.text()
    masterFileDir = mw.masterFolderPath_lineedit.text()
    dataFileDir = mw.dataFolderPath_lineedit.text()
    # Initiate Class parameters
    initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)
    DE_saleFiles = os.path.join(dataFileDir, "a21","2.1a_*.csv.gz")
    saleFilePath = os.path.join(saleFileDir, '*.csv.gz')
    stockFilePath = os.path.join(stockFileDir, '*.csv.gz')

    df = pl.scan_csv(saleFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
    df = removeWarehouseSale(df)
    df01 = df[['Posting Date','Location Code','SaleQty','CostValue','SaleValue','Unit Price Including VAT','Brand Code','StoreName','City','Country','Season Code']]
    df01 = df01.with_columns(pl.col("Country").replace_strict(exRate, default=None).alias('ExchRate'))
    df01 = df01.with_columns(pl.col('Posting Date').dt.year().alias('Year'))
    df01 = df01.with_columns(pl.col('Posting Date').dt.month().alias('tmpMonth'))
    df01 = df01.with_columns(pl.col("tmpMonth").replace_strict(monthDict, default=None).alias('Month'))
    df01 = df01.filter(pl.col('Country').ne('0'))
    df01 = df01.with_columns((pl.col("SaleValue") * pl.col("ExchRate")).alias("Sale Amt(AED)"))
    df01 = df01.with_columns((pl.col("CostValue") * pl.col("ExchRate")).alias("COGS(AED)"))
    df01 = df01.with_columns((pl.col("SaleQty") * pl.col("Unit Price Including VAT") * pl.col("ExchRate")).alias("Original Amount(AED)"))
    df01 = df01.with_columns((pl.col("Sale Amt(AED)") - pl.col("COGS(AED)")).alias("Margin Amount(AED)"))
    df01 = df01.with_columns((pl.col("Original Amount(AED)") - pl.col("Sale Amt(AED)")).alias("Discount Amount(AED)"))
    index=['Year','Month','Posting Date','Country','Location Code','StoreName','Brand Code']    #,'Season Code'
    values=['SaleQty','Sale Amt(AED)','COGS(AED)','Original Amount(AED)','Margin Amount(AED)','Discount Amount(AED)']
    df02 = df01.group_by(index).agg(pl.sum(values),).fill_null(0).fill_nan(0)
    df02 = df02.with_columns((pl.col('Country') + pl.col('Location Code').cast(pl.String) + pl.col('Posting Date').cast(pl.String)).alias('LookupIndex'))
    #---------------------------------------------------------------------------------------------------------------------
    df_kpi = pl.scan_csv(ashc.kpiFile, infer_schema_length=0,).fill_null(0).fill_nan(0).collect()
    df_kpi = df_kpi.with_columns(pl.col("Location Name").replace_strict(ashc.LocCode, return_dtype=pl.String, default=None).alias('Location Code'))
    df_kpi = df_kpi.with_columns(pl.col('Date').str.to_datetime(format='%d/%m/%Y').alias('Posting Date'))
    df_kpi = df_kpi.with_columns(pl.col('Visitors').str.strip_chars().str.replace('"',''))
    df_kpi = df_kpi.with_columns(pl.col('Visitors').str.strip_chars().str.replace(',','').cast(pl.Int64))
    df_kpi = df_kpi.with_columns(pl.col('Buyers').str.strip_chars().str.replace('"',''))
    df_kpi = df_kpi.with_columns(pl.col('Buyers').str.strip_chars().str.replace(',','').cast(pl.Int64))
    df_kpi = df_kpi.with_columns(pl.col('Target').str.strip_chars().str.replace('"',''))
    df_kpi = df_kpi.with_columns(pl.col('Target').str.strip_chars().str.replace(',',''))
    df_kpi = df_kpi.with_columns(pl.col('Target').str.strip_chars().str.replace(',','').cast(pl.Int64))
    df_kpi = df_kpi.with_columns(pl.col("Posting Date").replace_strict(ashc.Week_, return_dtype=pl.String, default=None).alias('MerchWeek'))
    df_kpi = df_kpi.with_columns(pl.col("Posting Date").replace_strict(ashc.Year_, return_dtype=pl.String, default=None).alias('Year'))
    df_kpi = df_kpi.with_columns(pl.col("Posting Date").replace_strict(ashc.Month_, return_dtype=pl.String, default=None).alias('Month'))
    df_kpi = df_kpi.with_columns(pl.col("Posting Date").replace_strict(ashc.Qtr_, return_dtype=pl.String, default=None).alias('Quarter'))
    df_kpi = df_kpi.with_columns(pl.col("Posting Date").replace_strict(ashc.Lyty_, return_dtype=pl.String, default=None).alias('Comp'))
    df_kpi = df_kpi.with_columns(pl.col("Location Code").replace_strict(ashc.ShortStoreName, return_dtype=pl.String, default=None).alias('ShortName'))
    df_kpi = df_kpi.with_columns(pl.col("Location Code").replace_strict(ashc.LocationType, return_dtype=pl.String, default=None).alias('Location Type'))
    df_kpi = df_kpi.with_columns(pl.col("Location Code").replace_strict(ashc.City, return_dtype=pl.String, default=None).alias('City'))
    df_kpi = df_kpi.with_columns(pl.col("Location Code").replace_strict(ashc.Country, return_dtype=pl.String, default=None).alias('Country'))
    df_kpi = df_kpi.with_columns(pl.col("Location Code").replace_strict(ashc.BrandName, return_dtype=pl.String, default=None).alias('Brand Code'))
    df_kpi = df_kpi.with_columns(pl.col("Location Code").replace_strict(ashc.StoreName, return_dtype=pl.String, default=None).alias('StoreName'))
    df_kpi = df_kpi[['Posting Date','Country','Location Code','Visitors','Buyers','Target']]
    df_kpi = df_kpi.with_columns((pl.col('Country') + pl.col('Location Code').cast(pl.String) + pl.col('Posting Date').cast(pl.String)).alias('LookupIndex'))
    df_kpi = df_kpi.filter(pl.col("LookupIndex").ne(""))
    df_kpi = df_kpi.fill_null(0).fill_nan(0)
    df_kpi = df_kpi.with_columns((pl.col('Visitors') + pl.col('Buyers') + pl.col('Target')).alias('Filter2'))
    df_kpi = df_kpi.filter(pl.col("Filter2").ne(0))
    df_kpi = df_kpi[["LookupIndex","Visitors","Buyers","Target"]]
    #---------------------------------------------------------------------------------------------------------------------
    extract_columns = ['Date','Type','Company Name','Country','Brand Code','Department','Profit Centre Code','Location Name','Store Opening Date','Store Size','Date Day Description','I Ns','OU Ts','Quantity','Sales Amount LCY','Sales Amount BASE','Target Amount BASE','Amount Tendered BASE']
    df_DE = pl.scan_csv(DE_saleFiles,).fill_null(0).fill_nan(0).collect()
    df_DE = df_DE.with_columns(pl.col('Date').str.to_datetime(format='%d/%m/%Y').alias('Date'))
    df_DE01 = df_DE[extract_columns]
    df_DE01 = df_DE01.rename({'Date':'Posting Date','Department':'Division','Profit Centre Code':'Location Code','Location Name':'StoreName','Quantity':'SaleQty','Sales Amount BASE':'Sale Amt(AED)'})
    df_DE01 = df_DE01.with_columns(pl.col("Location Code").map_elements(lambda x: str(x).replace(".0","")[-4:], return_dtype=pl.String).alias('Location Code'),)
    pvt_index=['Posting Date','Company Name','Country','Brand Code','Division','Location Code','StoreName']
    pvt_values=['SaleQty','Sale Amt(AED)']
    df_DE01 = df_DE01.group_by(pvt_index).agg(pl.sum(pvt_values)).fill_null(0).fill_nan(0)
    df_DE01 = df_DE01.with_columns((df_DE01['Sale Amt(AED)'] / df_DE01['SaleQty']).alias('Unit Price Including VAT'))
    df_DE01 = df_DE01.filter(pl.col('Brand Code').eq('DE'))
    df_DE01 = df_DE01.with_columns((pl.col('Country') + pl.col('Location Code').cast(pl.String) + pl.col('Posting Date').cast(pl.String)).alias('LookupIndex'))
    df_DE01 = df_DE01.filter(pl.col("LookupIndex").ne(""))
    df_DE01 = df_DE01.fill_null(0).fill_nan(0)
    df_DE01 = df_DE01.with_columns(pl.col("Posting Date").replace_strict(ashc.Year_, return_dtype=pl.Int32, default=None).alias('Year'))
    df_DE01 = df_DE01.with_columns(pl.col("Posting Date").replace_strict(ashc.Month_, return_dtype=pl.String, default=None).alias('Month'))
    df_DE01 = df_DE01.with_columns(pl.col('SaleQty').cast(pl.Float32))
    df_DE01 = df_DE01.with_columns(pl.lit(0.0).alias('COGS(AED)'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0.0).alias('Original Amount(AED)'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0.0).alias('Margin Amount(AED)'),)
    df_DE01 = df_DE01.with_columns(pl.lit(0.0).alias('Discount Amount(AED)'),)
    df_DE01 = df_DE01[["Year","Month","Posting Date","Country","Location Code","StoreName","Brand Code","SaleQty","Sale Amt(AED)","COGS(AED)","Original Amount(AED)","Margin Amount(AED)","Discount Amount(AED)","LookupIndex"]]
    #---------------------------------------------------------------------------------------------------------------------
    df_01 = pl.concat([df02,df_DE01], how="diagonal").fill_null(0).fill_nan(0)
    idx = ["LookupIndex","Year","Month","Posting Date","Country","Location Code","StoreName","Brand Code"]
    val = ["SaleQty","Sale Amt(AED)","COGS(AED)","Original Amount(AED)","Margin Amount(AED)","Discount Amount(AED)"]
    df_02 = df_01.group_by(idx).agg(pl.sum(val)).fill_null(0).fill_nan(0)
    df_02 = df_02.with_columns(pl.col("Location Code").replace_strict(ashc.LocationType, return_dtype=pl.String, default=None).alias("Location Type"))
    df_02 = df_02.with_columns(pl.col("Location Code").replace_strict(ashc.ShortStoreName, return_dtype=pl.String, default=None).alias("ShortName"))
    df_02 = df_02.with_columns(pl.col("Posting Date").replace_strict(ashc.Week_, return_dtype=pl.String, default=None).alias("MerchWeek"))
    df_02 = df_02.with_columns((pl.col("Location Code").cast(pl.String) + pl.col("MerchWeek").cast(pl.String)).alias("LFLLookup"))
    df_02 = df_02.with_columns(pl.col("LFLLookup").replace_strict(ashc.Lfl, return_dtype=pl.String, default=None).alias("LFL_Status"))
    df_02 = df_02.join(df_kpi, on="LookupIndex", how="left").fill_null(0)
    df_02 = df_02.drop(pl.col("LookupIndex"))
    df_02 = df_02.drop(pl.col("LFLLookup"))
    df_02.write_csv(os.path.join(mw.output_folder,"All.csv"), separator=",")
    all_text = all_text + f"Sale Summary Report Completed\n"
    progress_callback.emit(all_text)
    mw.infotextmisc_lable.setText(r"Sale Summary Report Completed")
    return "Done"