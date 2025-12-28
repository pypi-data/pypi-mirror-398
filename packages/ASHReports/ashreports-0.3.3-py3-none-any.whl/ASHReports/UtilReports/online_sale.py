import polars as pl
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig


def OnlineMPReport(mw, progress_callback):
        all_text = ""
        all_text = all_text + "Started MP Online Report Process\n"
        progress_callback.emit(all_text)
        mw.infotextmisc_lable.setText(r"Started MP Online Report Process")

        sale_Folder = "C:\\Reports\\Output\\StyleSummary\\*.csv"
        platform_name = {"JC-Web":"Web","UZ-Namshi":"Namshi and Noon","OK-Web":"Web","VI-SixthS":"6th Street","PA-SixthS":"6th Street",
                         "VI-Namshi":"Namshi and Noon","PA-Sixth":"6th Street","PA-Namshi":"Namshi and Noon","YR-SixthS":"6th Street",
                         "YR-Namshi":"Namshi and Noon","OK-Namshi":"Namshi and Noon","YR-Noon":"Namshi and Noon","LS-Namshi":"Namshi and Noon",
                         "PA-Online":"Web","VI-Amazon":"Namshi and Noon","LS-HO":"Web","OK-SixthS":"6th Street"}
        
        pIdx = ["Country","Location Code","StoreName","ShortName","Location Type","Year","Month","MerchWeek","Brand Code","Style Code",
                "Colour Code","Season Code","Division","Product Group","Item Category","Item Class","Item Sub Class","Sub Class","Theme",
                "Remarks","YTD","WTD","Unit_Price"]
        
        pVal = ["Total Purchase Qty","Closing Stock","Total Stock Cost(AED)","Total Stock Retail(AED)","SaleQty","Total Sale Cost(AED)",
                "Total Sale Retail(AED)","Total Sale Org. Retail(AED)","Discount Value","GrossMargin Value"]

        df_sls = pl.scan_csv(sale_Folder, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
        df_sls = df_sls.filter(pl.col('Country').ne('0'))
        df_sls = df_sls.filter(pl.col('Style Code').ne('111'))
        df_sls = df_sls.filter(pl.col('Year').eq(2025))
        df_sls = df_sls.filter(pl.col('Location Type').eq('Online'))

        df = df_sls.group_by(pIdx).agg(pl.mean('Unit_Cost'), pl.sum(pVal),)
        df = df.with_columns(pl.col('Country').replace_strict(mw.exch_rate, default=None).alias('ExchRate'))
        df = df.with_columns(pl.col('ShortName').replace_strict(platform_name, default=None).alias('Platform Name'))

        df.write_csv(f"C:\\Reports\\Output\\Online_Sale.csv",)
        mw.infotextmisc_lable.setText(r"MP Online Report Process ended")
        return "Done..."
