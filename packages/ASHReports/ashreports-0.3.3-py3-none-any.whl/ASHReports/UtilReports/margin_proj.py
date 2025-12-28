import polars as pl
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig

def MarginProjection(mw, progress_callback):
        all_text = ""
        all_text = all_text + "Starting Report Process\n"
        progress_callback.emit(all_text)
        mw.infotextmisc_lable.setText(r"Started Report Process")

        saleFilePath = "C:\\Reports\\Output\\Combined\\*.csv"
        offer_list = "C:\\Reports\\Data\\Configs\\Offer_Detail.csv"
        df_offeList = pl.read_csv(offer_list, infer_schema_length=0,).fill_null(0)
        df_offeList = df_offeList.select(["Combo","Offer","Sale Disc%","Actual_Offer"])

        # Get all user inputs
        saleFileDir = mw.saleReportPath_lineedit.text()
        stockFileDir = mw.stockReportPath_lineedit.text()
        masterFileDir = mw.masterFolderPath_lineedit.text()
        dataFileDir = mw.dataFolderPath_lineedit.text()
        # Initiate Class parameters
        initiateConfig(saleFileDir, stockFileDir, masterFileDir, dataFileDir, mw.output_folder)

        df = pl.scan_csv(saleFilePath, schema_overrides=ashc.dataTypeForAll,).fill_null(0).fill_nan(0).collect()
        df = df.filter(pl.col('Country').ne('0'))
        df = df.filter(pl.col('Location Type').is_in(['Store','Warehouse']))
        df = df.filter(pl.col('Season Code').is_in(mw.Sellthru_Season_Filter))

        df = df.with_columns((df['Cumm. CostValue'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('Cumm. CostValue'))
        df = df.with_columns((df['MTD CostValue'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('MTD CostValue'))
        df = df.with_columns((df['WTD CostValue'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('WTD CostValue'))

        df = df.with_columns((df['Cumm. SaleValue'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('Cumm. SaleValue'))
        df = df.with_columns((df['MTD SaleValue'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('MTD SaleValue'))
        df = df.with_columns((df['WTD SaleValue'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('WTD SaleValue'))

        df = df.with_columns((df['Cumm. SaleQty'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32) * df['Unit Price'].cast(pl.Float32)).alias('Cumm.SaleOrg'))
        df = df.with_columns((df['MTD SaleQty'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32) * df['Unit Price'].cast(pl.Float32)).alias('MTD SaleOrg'))
        df = df.with_columns((df['WTD SaleQty'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32) * df['Unit Price'].cast(pl.Float32)).alias('WTD SaleOrg'))

        df = df.with_columns((df['StockCost'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('StockCost'))
        df = df.with_columns((df['StockRetail'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('StockRetail'))
        df = df.with_columns((df['StockOrgRetail'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32)).alias('StockOrgRetail'))

        pIdx = ["Brand Code","Country","Division","Product Group","Item Category","Item Class","Item No_","ExchangeRate(AED)","Unit Price","RefCode","Style Code","Colour Code","Season Code","Remarks"]
        pVal = ["Cumm. SaleQty","Cumm. CostValue","Cumm. SaleValue","Cumm.SaleOrg","MTD SaleQty","MTD CostValue","MTD SaleValue","MTD SaleOrg","WTD SaleQty","WTD CostValue","WTD SaleValue","WTD SaleOrg","Closing Stock","StockCost","StockRetail","StockOrgRetail","Purchased"]

        df = df.group_by(pIdx).agg(pl.mean('StoreSize'), pl.sum(pVal),)
        df = df.with_columns(pl.col('Season Code').replace_strict(mw.Sellthru_common_Seasons, return_dtype=pl.String, default=None).alias('Season'))
        df = df.with_columns(pl.col('Remarks').replace_strict(mw.Sellthru_Season_Remarks, return_dtype=pl.String, default=None).alias('Season Type'))
        df = df.filter(pl.col('Brand Code').is_in(['JC','UZ','VI','PA','OK']))
        df = df.with_columns((df['Brand Code'].cast(pl.String) + df['Country'].cast(pl.String) + df['Item No_'].cast(pl.String)).alias('Combo'))
        df = df.join(df_offeList, on="Combo", how="left")
        df = df.with_columns(df['Offer'].fill_null("FP"))
        df = df.with_columns(df['Sale Disc%'].fill_null("0%"))
        df = df.with_columns(df['Actual_Offer'].fill_null("NA"))
        df = df.with_columns(df['Sale Disc%'].str.replace_all('%','',literal=True).cast(pl.Float32).alias('Sale Disc%'))
        df = df.with_columns((df['Sale Disc%'] / 100).alias('Sale Disc%')).fill_nan(0)
        df = df.with_columns((df['Closing Stock'].cast(pl.Float32) * df['ExchangeRate(AED)'].cast(pl.Float32) * df['Unit Price'].cast(pl.Float32) * df['Sale Disc%'].cast(pl.Float32)).alias('Disc. Val'))
        df = df.with_columns((df['StockOrgRetail'].cast(pl.Float32) - df['Disc. Val'].cast(pl.Float32)).alias('StockDiscRetail'))

        df.write_csv(f"C:\\Reports\\Output\\SaleListData.csv",)
        mw.infotextmisc_lable.setText(r"Done...")

        return "Done..."