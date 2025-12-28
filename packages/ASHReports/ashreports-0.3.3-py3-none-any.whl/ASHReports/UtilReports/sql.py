import os, glob, shutil, gzip
import pandas as pd
from io import StringIO
from pathlib import PureWindowsPath, PurePosixPath
from PySide6.QtWidgets import QFileDialog

def selectBrands(mw):
    brandList = []
    if mw.jacadi_checkBox.isChecked():
        brandList.append("JC")

    if mw.okaidi_checkBox.isChecked():
        brandList.append("OK")

    if mw.parfois_checkBox.isChecked():
        brandList.append("PA")

    if mw.undiz_checkBox.isChecked():
        brandList.append("UZ")

    if mw.vincci_checkBox.isChecked():
        brandList.append("VI")

    if mw.yves_checkBox.isChecked():
        brandList.append("YR")

    if mw.lsr_checkBox.isChecked():
        brandList.append("LS")

    return brandList

def stockSQL(mw, progress_callback):
    all_text = f"stockSQL\n"
    progress_callback.emit(all_text)
    stkAsOn = mw.stkStart_dateedit.date()
    dt01 = stkAsOn.toPython()
    stkPostDate = mw.stkEnd_dateedit.date()
    dt02 = stkPostDate.toPython()
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderStock, f"ClosingStock-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT ve.[Location Code],ve.[Item No_], SUM(ve.[Invoiced Quantity]) AS 'Closing Stock',\n i.[Brand Code], i.[Style Code], i.[Item Category Code] AS 'Item Category',\n i.[Product Group Code] AS 'Product Group', i.[Division Code] AS 'Division',\n i.[Description], i.[Season Code], i.[Colour Code], i.[Sub Class],i.[Item Class],\n i.[Item Sub Class], loc.[Name] AS 'StoreName', loc.[City], loc.[Country_Region Code] AS 'Country',\n i.[Unit Cost], i.[Unit Price], ex.Size AS 'Size', cp.[Sale Price] AS 'Current Retail Price',\n'{dt02} 00:00:00.000' AS 'Posting Date'\nFROM dbo.[{db}$Value Entry] ve WITH (NOLOCK)\nLEFT OUTER JOIN dbo.[{db}$Item] i WITH (NOLOCK) ON ve.[Item No_] = i.[No_]\nLEFT OUTER JOIN dbo.[{db}$Location] loc  ON ve.[Location Code] = loc.[Code]\nOUTER APPLY (\n  SELECT TOP 1\n  CONVERT(VARCHAR, Value) AS Size\n  FROM dbo.[{db}$Extended Variant Values] WITH (NOLOCK)\n  WHERE [Item No_] = ve.[Item No_]\n  AND Code = 'SIZE') ex\nLEFT OUTER JOIN dbo.[{db}$Item Current Price] cp WITH (NOLOCK) ON ve.[Item No_] = cp.[Item No_]\nWHERE ve.[Posting Date] <= '{dt01} 00:00:00.000'\nGROUP BY\n ve.[Location Code],ve.[Item No_],i.[Brand Code],i.[Style Code],i.[Item Category Code],i.[Product Group Code],\n i.[Division Code],i.[Description],i.[Season Code],i.[Colour Code],i.[Sub Class],i.[Item Class],\n i.[Item Sub Class],loc.[Name],loc.[City],loc.[Country_Region Code],i.[Unit Cost],i.[Unit Price],\n ex.Size,cp.[Sale Price]\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("Stock SQL Done...")
    mw.infotextsql_lable.setText(r"Stock SQL Done...")
    return "Done"

def saleSQL(mw, progress_callback):
    all_text = f"saleSQL\n"
    progress_callback.emit(all_text)
    slsStart = mw.slsStart_dateedit.date()
    start_dt = slsStart.toPython()
    slsEnd = mw.slsEnd_dateedit.date()
    end_dt = slsEnd.toPython()
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderSale, f"Sale-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT ve.[Posting Date], ve.[Location Code], ve.[Item No_],(ve.[Invoiced Quantity] * -1) AS 'SaleQty',\n (ve.[Cost Amount (Actual)] * -1) AS 'CostValue',ve.[Sales Amount (Actual)] AS 'SaleValue',it.[Unit Price Including VAT],\n it.[Season Code],it.[Brand Code],it.[Style Code],it.[Colour Code],it.[Sub Class],it.[Item Class],it.[Item Sub Class],\n it.[Item Category Code] AS 'Item Category',it.[Product Group Code] AS 'Product Group',it.[Division Code] AS 'Division',\n it.[Description],loc.[Name] AS 'StoreName',loc.[City] AS 'City',loc.[Country_Region Code] AS 'Country',\n (SELECT TOP 1 CONVERT(VARCHAR, Value)\nFROM dbo.[{db}$Extended Variant Values] WITH (NOLOCK)\nWHERE [Item No_] = it.[No_] AND Code = 'SIZE') AS 'Size'\nFROM dbo.[{db}$Value Entry] ve WITH (NOLOCK)\nLEFT OUTER JOIN [ASH_LIVE01].[dbo].[{db}$Item] it WITH (NOLOCK) ON ve.[Item No_] = it.[No_]\nLEFT OUTER JOIN [ASH_LIVE01].[dbo].[{db}$Location] loc WITH (NOLOCK) ON ve.[Location Code] = loc.[Code]\nWHERE ve.[Posting Date] BETWEEN '{start_dt} 00:00:00.000' AND '{end_dt} 00:00:00.000'\nAND ve.[Item Ledger Entry Type] = 1\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("Sale SQL Done...")
    mw.infotextsql_lable.setText(r"Sale SQL Done...")
    return "Done"

def firstpurchaseSQL(mw, progress_callback):
    all_text = f"firstpurchaseSQL\n"
    progress_callback.emit(all_text)
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderFirstPurchase, f"FirstPurchase-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT a.[Item No_],SUM(a.[Remaining Quantity]),a.[Location Code],min(b.[Posting Date]) First_purchase_date, max(a.[Last Invoice Date]) Last_purchase_date  FROM dbo.[{db}$Item Ledger Entry] a\nLEFT OUTER JOIN dbo.[{db}$Purch_ Inv_ Line]  b\nON a.[Item No_]=b.No_\nGROUP BY a.[Item No_],a.[Location Code]\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("First purch. SQL Done...")
    mw.infotextsql_lable.setText(r"First purch. SQL Done...")
    return "Done"

def itempriceSQL(mw, progress_callback):
    all_text = f"Itemprice\n"
    progress_callback.emit(all_text)
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderFirstPurchase, f"ItemPrices-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT [Location Code],\n(SELECT [Country_Region Code] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = ve.[Location Code]) as 'Country',\n(SELECT [Name] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = ve.[Location Code]) as 'StoreName',\n(SELECT [Brand Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Brand Code',\n(SELECT [Style Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Style Code',\n(SELECT [Colour Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Colour Code',\n(SELECT top 1 CONVERT(VARCHAR,Value) FROM dbo.[{db}$Extended Variant Values] ex WHERE ex.[Item No_] = ve.[Item No_] and Code = 'SIZE') as 'Size',\n[Item No_],\n(SELECT [Season Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Season Code',\n(SELECT [Unit Cost] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Unit Cost',\n(SELECT [Unit Price] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Unit Price',\n(SELECT [Sale Price] FROM dbo.[{db}$Item Current Price] WHERE ve.[Item No_] = [Item No_]) as 'Current Retail Price'\nFROM dbo.[{db}$Value Entry] ve\nGROUP BY [Location Code], [Item No_]\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("Item price SQL Done...")
    mw.infotextsql_lable.setText(r"Item price SQL Done...")
    return "Done"

def purchaseSQL(mw, progress_callback):
    all_text = f"purchaseSQL\n"
    progress_callback.emit(all_text)
    slsStart = mw.slsStart_dateedit.date()
    start_dt = slsStart.toPython()
    slsEnd = mw.slsEnd_dateedit.date()
    end_dt = slsEnd.toPython()
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderPruchase, f"PurchaseDetail-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT c.[Location Code], c.[Posting Date], c.[No_] AS 'Item No_', c.[Buy-from Vendor No_],v.[Name] AS 'Vendor Name',\n it.[Brand Code],it.[Style Code],it.[Item Category Code] AS 'Item Category',it.[Product Group Code] AS 'Product Group',\n it.[Division Code] AS 'Division',it.[Description],it.[Colour Code],ev.[Value] AS 'Size',it.[Sub Class],it.[Item Class],\n it.[Item Sub Class],loc.[Name] AS 'StoreName',loc.[City],loc.[Country_Region Code] AS 'Country',c.[Quantity] AS 'Purchase Qty',\n c.[Direct Unit Cost],c.[Unit Cost (LCY)],c.[Unit Price (LCY)],\n (c.[Quantity] * c.[Direct Unit Cost]) AS 'Total Direct Unit Cost',\n (c.[Quantity] * c.[Unit Cost (LCY)]) AS 'Total Unit Cost (LCY)',\n (c.[Quantity] * c.[Unit Price (LCY)]) AS 'Total Unit Price (LCY)',\n it.[Season Code] AS 'Seasoncode_Item',c.[Season Code] AS 'Seasoncode_Purchase'\nFROM dbo.[{db}$Purch_ Inv_ Line] c\nLEFT JOIN dbo.[{db}$Item] it ON c.No_ = it.No_\nLEFT JOIN dbo.[{db}$Vendor] v ON c.[Buy-from Vendor No_] = v.[No_]\nLEFT JOIN dbo.[{db}$Location] loc ON loc.[Code] = c.[Location Code]\nLEFT JOIN dbo.[{db}$Extended Variant Values] ev ON c.No_ = ev.[Item No_] AND ev.Code = 'SIZE'\nWHERE c.[Posting Date] >= '{start_dt} 00:00:00.000'\nAND c.[Posting Date] <= '{end_dt} 00:00:00.000'\n\nUNION ALL\n\nSELECT c.[Location Code], c.[Posting Date], c.[No_] AS 'Item No_', c.[Buy-from Vendor No_], v.[Name] AS 'Vendor Name',\n it.[Brand Code],it.[Style Code],it.[Item Category Code] AS 'Item Category',it.[Product Group Code] AS 'Product Group',\n it.[Division Code] AS 'Division',it.[Description],it.[Colour Code],ev.[Value] AS 'Size',it.[Sub Class],it.[Item Class],\n it.[Item Sub Class],loc.[Name] AS 'StoreName',loc.[City],loc.[Country_Region Code] AS 'Country',c.[Quantity] AS 'Purchase Qty',\n c.[Direct Unit Cost],c.[Unit Cost (LCY)],c.[Unit Price (LCY)],\n (c.[Quantity] * c.[Direct Unit Cost]) * -1 AS 'Total Direct Unit Cost',\n (c.[Quantity] * c.[Unit Cost (LCY)]) * -1 AS 'Total Unit Cost (LCY)',\n (c.[Quantity] * c.[Unit Price (LCY)]) * -1 AS 'Total Unit Price (LCY)',\n it.[Season Code] AS 'Seasoncode_Item', c.[Season Code] AS 'Seasoncode_Purchase'\nFROM dbo.[{db}$Purch_ Cr_ Memo Line] c\nLEFT JOIN dbo.[{db}$Item] it ON c.No_ = it.No_\nLEFT JOIN dbo.[{db}$Vendor] v ON c.[Buy-from Vendor No_] = v.[No_]\nLEFT JOIN dbo.[{db}$Location] loc ON loc.[Code] = c.[Location Code]\nLEFT JOIN dbo.[{db}$Extended Variant Values] ev ON c.No_ = ev.[Item No_] AND ev.Code = 'SIZE'\nWHERE c.[Posting Date] >= '{start_dt} 00:00:00.000'\nAND c.[Posting Date] <= '{end_dt} 00:00:00.000'\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("Purch. SQL Done...")
    mw.infotextsql_lable.setText(r"Purch. SQL Done...")
    return "Done"

def saleofferSQL(mw, progress_callback):
    all_text = f"saleofferSQL\n"
    progress_callback.emit(all_text)
    slsStart = mw.slsStart_dateedit.date()
    start_dt = slsStart.toPython()
    slsEnd = mw.slsEnd_dateedit.date()
    end_dt = slsEnd.toPython()
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderSaleOffer, f"SaleOffer-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT [Trans_ Date] as 'Posting Date',[Store No_]+cast([Transaction No_] as varchar)+cast([Receipt No_] as varchar) as 'LookupCombo',[Transaction No_],[Receipt No_],[Store No_] as 'Location Code',[Item No_],[Brand Code],[Style Code],[Colour Code],[Size Code] as 'Size',[Season Code],\n(SELECT [Item Category Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Item Category',\n(SELECT [Product Group Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Product Group',\n(SELECT [Division Code] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Division',\n(SELECT [Description] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Description',\n(SELECT [Sub Class] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Sub Class',\n(SELECT [Item Class] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Item Class',\n(SELECT [Item Sub Class] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Item Sub Class',\n(SELECT [Name] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = ve.[Store No_]) as 'StoreName',\n(SELECT [City] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = ve.[Store No_]) as 'City',\n(SELECT [Country_Region Code] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = ve.[Store No_]) as 'Country',\n(SELECT [Unit Price Including VAT] FROM dbo.[{db}$Item] WHERE ve.[Item No_] = [No_]) as 'Unit Price Including VAT',\n(SELECT [Description] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Description',\n(SELECT [Priority] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Priority',\n(SELECT [Validation Period ID] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Validation Period',\n(SELECT [Last Date Modified] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Last Modified',\n(SELECT [Currency Code] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Currency Code',\n(SELECT [Price Group] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Price Group',\n(SELECT [Coupon Code] FROM dbo.[{db}$Periodic Discount] WHERE ve.[Periodic Disc_ Group] = [No_]) as 'Offer Coupon Code',\n[Periodic Disc_ Type],[Periodic Disc_ Group] as 'Offer Code',([Quantity]*-1) as 'SaleQty',([Cost Amount]*-1) as 'CostValue',([Total Rounded Amt_]*-1) as 'SaleValue',([Price]*([Quantity]*-1)) as 'OriginalValue',[Discount Amount] as 'Discount Value',[Line was Discounted]\nFROM dbo.[{db}$Trans_ Sales Entry] ve\nWHERE [Trans_ Date] >= '{start_dt} 00:00:00.000'\nAND [Trans_ Date] <= '{end_dt} 00:00:00.000'\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""

    mw.infotextsql_lable.setText(r"Sale Offer SQL Done...")
    return "Done"

def saleofferSQL1(mw, progress_callback):
    all_text = f"saleofferSQL1\n"
    progress_callback.emit(all_text)
    slsStart = mw.slsStart_dateedit.date()
    start_dt = slsStart.toPython()
    slsEnd = mw.slsEnd_dateedit.date()
    end_dt = slsEnd.toPython()
    brList = selectBrands(mw)
    for bru in brList:
        outFileDataPart1 = ""
        outFileDataPart2 = ""
        filePath = os.path.join(mw.outFolderSaleOffer, f"SaleOffer-{bru}.txt")
        outFileDataPart1 = outFileDataPart1 + f"WITH "
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileDataPart1 = outFileDataPart1 + f"{db[-3:]}_query1 AS (SELECT TR.[Trans_ Date] as 'Posting Date', TR.[Store No_]+cast(TR.[Transaction No_] as varchar)+cast(TR.[Receipt No_] as varchar) as 'LookupCombo', TR.[Transaction No_], TR.[Receipt No_], TR.[Store No_] as 'Location Code', TR.[Item No_], TR.[Brand Code],TR.[Style Code],TR.[Colour Code],TR.[Size Code] as 'Size',TR.[Season Code],TR.[Periodic Disc_ Group] as 'Offer Code',\n(SELECT [Item Category Code] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Item Category',\n(SELECT [Product Group Code] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Product Group',\n(SELECT [Division Code] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Division',\n(SELECT [Description] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Description',\n(SELECT [Sub Class] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Sub Class',\n(SELECT [Item Class] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Item Class',\n(SELECT [Item Sub Class] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Item Sub Class',\n(SELECT [Name] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = TR.[Store No_]) as 'StoreName',\n(SELECT [City] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = TR.[Store No_]) as 'City',\n(SELECT [Country_Region Code] FROM dbo.[{db}$Location] loc WHERE loc.[Code] = TR.[Store No_]) as 'Country',\n(SELECT [Unit Price Including VAT] FROM dbo.[{db}$Item] WHERE TR.[Item No_] = [No_]) as 'Unit Price Including VAT',\n(SELECT [Description] FROM dbo.[{db}$Periodic Discount] WHERE TR.[Periodic Disc_ Group] = [No_]) as 'Offer Description',\n(SELECT [Offer Type] FROM dbo.[{db}$Periodic Discount] WHERE TR.[Periodic Disc_ Group] = [No_]) as 'Offer Type',\n(SELECT [Validation Period ID] FROM dbo.[{db}$Periodic Discount] WHERE TR.[Periodic Disc_ Group] = [No_]) as 'Offer Validation Period',\n(SELECT [Last Date Modified] FROM dbo.[{db}$Periodic Discount] WHERE TR.[Periodic Disc_ Group] = [No_]) as 'Offer Last Modified',\n(SELECT [Discount _ Value] FROM dbo.[{db}$Periodic Discount] WHERE TR.[Periodic Disc_ Group] = [No_]) as 'Offer Discount',\n(SELECT [Deal Price Value] FROM dbo.[{db}$Periodic Discount] WHERE TR.[Periodic Disc_ Group] = [No_]) as 'Deal Price Value',\nCE.[Coupon Code],\nTR.[Periodic Disc_ Type],\n(TR.[Quantity]*-1) as 'SaleQty',\n(TR.[Cost Amount]*-1) as 'CostValue',\n(TR.[Total Rounded Amt_]*-1) as 'SaleValue',\n(TR.[Price]*TR.[Quantity]*-1) as 'OriginalValue',\nTR.[Discount Amount] as 'Discount Value',\nTR.[Line was Discounted]\nFROM dbo.[{db}$Trans_ Sales Entry] TR\nINNER JOIN dbo.[{db}$Trans_ Coupon Entry] CE\nON TR.[Store No_] = CE.[Store No_]\n  AND TR.[POS Terminal No_] = CE.[POS Terminal No_]\n  AND CAST(TR.[Transaction No_] AS VARCHAR) = CAST(CE.[Transaction No_] AS VARCHAR)\n  AND CAST(TR.[Receipt No_] AS VARCHAR) = CAST(CE.[Receipt No_] AS VARCHAR)\nWHERE TR.[Trans_ Date] BETWEEN '{start_dt} 00:00:00.000' AND '{end_dt} 00:00:00.000'),\n{db[-3:]}_query2 AS (Select FF.[Validation Period ID],\n(SELECT [Description] FROM dbo.[{db}$Validation Period] WHERE FF.[Validation Period ID] = [ID]) as 'Validation Description',\n(SELECT [Starting Date] FROM dbo.[{db}$Validation Period] WHERE FF.[Validation Period ID] = [ID]) as 'Offer_Start_Date',\n(SELECT [Ending Date] FROM dbo.[{db}$Validation Period] WHERE FF.[Validation Period ID] = [ID]) as 'Offer_End_Date'\nFrom dbo.[{db}$Periodic Discount] FF),"
        outFileDataPart1 = outFileDataPart1[:-1]
        part1_lines = StringIO(outFileDataPart1).readlines()

        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileDataPart2 = outFileDataPart2 + f"\nSELECT Q1.[Posting Date],\nQ1.[LookupCombo],\nQ1.[Transaction No_],\nQ1.[Receipt No_],\nQ1.[Location Code],\nQ1.[Brand Code],\nQ1.[Item No_],\nQ1.[Style Code],\nQ1.[Colour Code],\nQ1.[Size],\nQ1.[Line was Discounted],\nQ1.[Season Code],\nQ1.[Coupon Code],\nQ1.[Offer Code],\nQ1.[Offer Description],\nQ1.[Offer Type],\nQ1.[Offer Validation Period],\nQ2.[Validation Description],\nQ2.[Offer_Start_Date],\nQ2.[Offer_End_Date],\nQ1.[Offer Last Modified],\nQ1.[Offer Discount],\nQ1.[Deal Price Value],\nQ1.[Item Category],\nQ1.[Product Group],\nQ1.[Division],\nQ1.[Description],\nQ1.[Sub Class],\nQ1.[Item Class],\nQ1.[Item Sub Class],\nQ1.[StoreName],\nQ1.[City],\nQ1.[Country],\nQ1.[Unit Price Including VAT],\nQ1.[SaleQty],\nQ1.[CostValue],\nQ1.[SaleValue],\nQ1.[OriginalValue],\nQ1.[Discount Value]\nFROM {db[-3:]}_query1 Q1\nJOIN {db[-3:]}_query2 Q2 ON Q1.[Offer Validation Period] = Q2.[Validation Period ID]\n"
                outFileDataPart2 = outFileDataPart2 + "\nUNION ALL\n"

        part2_lines = StringIO(outFileDataPart2).readlines()
        part2_lines = part2_lines[:-2]

        lines = part1_lines + part2_lines

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("Sale Offer SQL Done...")
    mw.infotextsql_lable.setText(r"Sale Offer1 SQL Done...")
    return "Done"

def transferSQL(mw, progress_callback):
    all_text = f"transferSQL\n"
    progress_callback.emit(all_text)
    slsStart = mw.slsStart_dateedit.date()
    start_dt = slsStart.toPython()
    slsEnd = mw.slsEnd_dateedit.date()
    end_dt = slsEnd.toPython()
    brList = selectBrands(mw)
    for bru in brList:
        outFileData = ""
        filePath = os.path.join(mw.outFolderSaleOffer, f"TransferDetail-{bru}.txt")
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileData = outFileData + f"SELECT a.Remarks,[Document No_],b.[Item No_],b.[Quantity],b.[Shipment Date],b.[Transfer-from Code],b.[Transfer-to Code]\nFROM [dbo].[{db}$Transfer Shipment Header] a WITH (NOLOCK)\nLEFT OUTER JOIN [dbo].[{db}$Transfer Shipment Line] b WITH (NOLOCK) ON a.[No_] = b.[Document No_]\nWHERE b.[Posting Date] BETWEEN '{start_dt} 00:00:00.000' AND '{end_dt} 00:00:00.000'\nGROUP BY a.Remarks,[Document No_], b.[Item No_],b.[Quantity],b.[Shipment Date],b.[Transfer-from Code],b.[Transfer-to Code]\n"
                outFileData = outFileData + "\nUNION ALL\n\n"

        lines = StringIO(outFileData).readlines()
        lines = lines[:-3]

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")

            lines = ""
    print("Transfer SQL Done...")
    mw.infotextsql_lable.setText(r"Transfer SQL Done...")
    return "Done"

def activeOfferItemSQL(mw, progress_callback):
    all_text = f"activeOfferItemSQL\n"
    progress_callback.emit(all_text)
    brList = selectBrands(mw)
    for bru in brList:
        outFileDataPart1 = ""
        outFileDataPart2 = ""
        filePath = os.path.join(mw.outFolderSaleOffer, f"ActiveOfferItemDetail-{bru}.txt")
        outFileDataPart1 = outFileDataPart1 + f"WITH "
        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileDataPart1 = outFileDataPart1 + f"{db[-3:]}_query1 AS (SELECT AA.[Offer No_] as 'Offer No', BB.[Description] as 'Offer Description', BB.[Status] as 'Enable Status',BB.[Validation Period ID],BB.[Pop-up Line 1],'{br}' as 'Brand Code', AA.[No_] as 'Item No_', AA.[Description] as 'Item Description', AA.[Standard Price Including VAT], AA.[Price Group], AA.[Currency Code], AA.[No_ of Items Needed], AA.[Disc_ Type], AA.[Offer Price Including VAT], AA.[Discount Amount Including VAT]\nFROM dbo.[{db}$Periodic Discount Line] AA\nINNER JOIN dbo.[{db}$Periodic Discount] BB\nON AA.[Offer No_] = BB.[No_]),\n{db[-3:]}_query2 AS (Select FF.[ID], FF.[Starting Date], FF.[Ending Date], FF.[Description]\nFROM dbo.[{db}$Validation Period] FF),"
        outFileDataPart1 = outFileDataPart1[:-1]
        part1_lines = StringIO(outFileDataPart1).readlines()

        for db, br in mw.dbFiles.items():
            if br == bru:
                outFileDataPart2 = outFileDataPart2 + f"\nSELECT Q1.[Brand Code], Q1.[Offer No], Q1.[Offer Description], Q1.[Enable Status], Q1.[Validation Period ID], Q2.[Starting Date], Q2.[Ending Date], Q1.[Item No_],\nQ1.[Item Description], Q1.[Standard Price Including VAT], Q1.[Price Group], Q1.[Currency Code], Q1.[No_ of Items Needed], Q1.[Disc_ Type], Q1.[Offer Price Including VAT], Q1.[Discount Amount Including VAT]\nFROM {db[-3:]}_query1 Q1\nJOIN {db[-3:]}_query2 Q2 ON Q1.[Validation Period ID] = Q2.[ID]\nWHERE Q1.[Enable Status] = 1\n"
                outFileDataPart2 = outFileDataPart2 + "\nUNION ALL\n"

        part2_lines = StringIO(outFileDataPart2).readlines()
        part2_lines = part2_lines[:-2]

        lines = part1_lines + part2_lines

        with open(filePath, 'w') as f:
            for line in lines:
                f.write(f"{line}")
                
            lines = ""
    print("Active OfferItem SQL Done...")
    mw.infotextsql_lable.setText(r"Active OfferItem SQL Done...")
    return "Done"
'''
def selectDumpFolder(mw, progress_callback):
    all_text = f"selectDumpFolder\n"
    progress_callback.emit(all_text)
    file_path, filter_ = QFileDialog.getOpenFileName(mw, 'Pick Dump file')
    folder_path = os.path.dirname(os.path.abspath(file_path))
    mw.dumpFolderPath_lineedit.setText(f"{folder_path}")
    return "Done"
'''
def renameDumpFiles(mw, progress_callback):
    all_text = f"renameDumpFiles\n"
    progress_callback.emit(all_text)
    dumpFilePath = mw.dumpFolderPath_lineedit.text()
    posixFilePath = str(PurePosixPath(PureWindowsPath(dumpFilePath)))
    print(posixFilePath)
    fileList = glob.glob(posixFilePath)

    for item in fileList:
        print(f"Processing : {os.path.split(item)[-1]}", end = " - Saving as : ")
        mw.infotextsql_lable.setText(f"Processing : {os.path.split(item)[-1]}")
        df = pd.read_csv(item, encoding='latin1', low_memory=False)
        df.fillna(0, inplace=True)
        try:
            if list(df.columns).index('Brand Code') > 0:
                try:
                    idx1 = list(df.columns).index("Offer Code")
                    idx2 = list(df.columns).index("SaleQty")
                    if (idx1 > 0) and (idx2 > 0):
                        brName_ = list(df['Brand Code'].unique())
                        brName = " ".join([str(x) for x in brName_])
                        brName = brName.replace("A0","").strip()
                        dateRange = min(df['Posting Date'].unique()).split(" ")[0] + " - " + max(df['Posting Date'].unique()).split(" ")[0]
                        fileName_x = f"{brName}_SaleOfferReport({dateRange}).csv"
                        filePath = os.path.join(mw.saleOfferFolder,fileName_x)
                        print(fileName_x + '.gz')

                except ValueError as e:
                    try:
                        idx2 = list(df.columns).index("SaleQty")
                        if idx2 > 0:
                            brName_ = list(df['Brand Code'].unique())
                            brName = " ".join([str(x) for x in brName_])
                            brName = brName.replace("A0","").strip()
                            dateRange = min(df['Posting Date'].unique()).split(" ")[0] + " - " + max(df['Posting Date'].unique()).split(" ")[0]
                            fileName_y = f"{brName}_SalesReport(Q2-2025).csv"
                            filePath = os.path.join(mw.saleOutFolder,fileName_y)
                            print(fileName_y + '.gz')

                    except ValueError as e:
                        pass

        except ValueError as e:
            pass

        idx1 = 0
        idx2 = 0

        try:
            idx = list(df.columns).index("Closing Stock")
            if idx > 0:
                brName_ = list(df['Brand Code'].unique())
                brName = " ".join([str(x) for x in brName_])
                brName = brName.replace("A0","").strip()
                fileName = f"{brName}_StockReport(2025).csv"
                filePath = os.path.join(mw.stockOutFolder,fileName)
                print(fileName + '.gz')
                idx = 0
        except ValueError as e:
            pass

        try:
            idx = list(df.columns).index("Last_purchase_date")
            if idx > 0:
                df['Brand Code'] = df['Location Code'].apply(lambda x: x[:2])
                brName_ = list(df['Brand Code'].unique())
                brName = " ".join([str(x) for x in brName_])
                brName = brName.replace("A0","").strip()
                fileName = f"{brName}_FirstAndLastPurchaseData.csv"
                filePath = os.path.join(mw.firstPurchOutFolder,fileName)
                print(fileName + '.gz')
                idx = 0
        except ValueError as e:
            pass

        try:
            idx = list(df.columns).index("Purchase Qty")
            if idx > 0:
                brName_ = list(df['Brand Code'].unique())
                brName = " ".join([str(x) for x in brName_])
                brName = brName.replace("A0","").strip()
                fileName = f"{brName}_PurchaseData(2025).csv"
                filePath = os.path.join(mw.purchOutFolder,fileName)
                print(fileName + '.gz')
                idx = 0
        except ValueError as e:
            pass

        df = None
        try:
            with open(item, 'rb') as f_in:
                with gzip.open(filePath + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            os.remove(item)

        except FileExistsError as e:
            os.remove(filePath)
            with open(item, 'rb') as f_in:
                with gzip.open(filePath + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"{item} overwritten")
            pass
    
    return "Done"