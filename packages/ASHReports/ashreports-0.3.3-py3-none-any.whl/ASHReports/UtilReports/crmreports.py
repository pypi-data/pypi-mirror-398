import requests, os, sys, json, time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
import ASHC_v3 as ashc
from ASHC_v3.initiateConfig import initiateConfig

def CRMReport(mw, progress_callback):
    all_text = f"CRMReport\n"
    progress_callback.emit(all_text)
    
    stage2_headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding":"gzip, deflate, br, zstd",
        "Accept-Language":"en-GB,en;q=0.9,en-US;q=0.8,en-IN;q=0.7",
        "Connection":"keep-alive",
        "Cookie":"PODIDAKS=1757927854.285.3552.709349|4580cd5b74b92755f70d765d620e2d80; JSESSIONID=12AFE5BB77660EF8AC0BEED9349DCEA3; G_ENABLED_IDPS=google; _ga=GA1.2.2108095877.1755447542; _gid=GA1.2.1089913653.1755447542; _gat=1; _ga_YQ5GNLNM1N=GS2.2.s1755447543$o1$g1$t1755448285$j60$l0$h0",
        "Host":"asp.adelya.com",
        "Referer":"https://asp.adelya.com/loyaltyoperator/clients/specificContentWrapper.jsp?title=Statistiques%20YR%20UAE&goto=/AdelyaClientSpe/biwee/dashboards.jsp&ajax=true",
        "Sec-Fetch-Dest":"document",
        "Sec-Fetch-Mode":"navigate",
        "Sec-Fetch-Site":"none",
        "Sec-Fetch-User":"?1",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
        "sec-ch-ua":'"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":'"Windows"'
    }

    stage3_headers = {
        "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language":"en-GB,en;q=0.9,en-US;q=0.8,en-IN;q=0.7",
        "priority":"u=0, i",
        "referer":"https://asp.adelya.com/",
        "sec-ch-ua":'"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile":"?0",
        "sec-ch-ua-platform":"Windows",
        "sec-fetch-dest":"iframe",
        "sec-fetch-mode":"navigate",
        "sec-fetch-site":"cross-site",
        "sec-fetch-storage-access":"active",
        "upgrade-insecure-requests":"1",
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
    }

    stage4_headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,en-IN;q=0.7",
        "api-token": "a520f591-4415-487a-8c05-e13aeb8666c3",
        "Cookie": "ARRAffinitySameSite=c293f503daad936fa1fa0d10be9609a41b38706fd70610ea17e06b0e9499e135",
        "data-status": "ok",
        "data-storage-key": "d5512a97-ab03-4746-adb5-bf1448235fd1",
        "priority": "u=1, i",
        "referer": "https://www.biwee.fr/Tdb/a520f591-4415-487a-8c05-e13aeb8666c3",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-fetch-storage-access": "active",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
        "x-requested-with": "XMLHttpRequest"
    }
    pd_name = ["pivotDashboardItem1","pivotDashboardItem2","pivotDashboardItem3","pivotDashboardItem4","pivotDashboardItem5","chartDashboardItem1",
            "chartDashboardItem2","pieDashboardItem1","pieDashboardItem2","pieDashboardItem5","pieDashboardItem6","gridDashboardItem5",
            "gridDashboardItem3","gridDashboardItem6","gridDashboardItem7"]
    
    cke = mw.crmToken_lineedit.text()
    detail_sale_data = "DATE,STORE,CARDNUMBER,ID SALE,PRODUCT NAME,TYPE,PRODUCT CODE / COUPON CODE,QUANTITY,FINAL PRICE\n"
    gridDashboardItem7_data = "PRODUCT NAME,VALUE AMT,QUANTITY\n"
    gridDashboardItem6_data = "PRODUCT NAME,QUANTITY,VALUE AMT\n"
    chartDashboardItem2_data = "STORE NAME,VALUE,UNKNOWN\n"
    chartDashboardItem1_data = "STORE NAME,TYPE,Qty,UNKNOWN\n"
    pieDashboardItem1_data = "TYPE,STORE NAME,Qty\n"
    pieDashboardItem2_data = "STORE NAME,TYPE,VALUE\n"
    gridDashboardItem5_data = "STORE NAME,TYPE,VALUE\n"
    pieDashboardItem6_data = "VOUCHERS,VALUE,QTY\n"
    pieDashboardItem5_data = "STORE,MEMBER\n"
    pieDashboardItem6_data = "STORE NAME,VALUE,UNKNOWN\n"


    nUrl2 = "https://asp.adelya.com/AdelyaClientSpe/biwee/dashboard.jsp?guid=485f9013-b78c-48ae-b129-b2501a166ad1"
    parameter_2 = {"Filter":[{"dimensions":[{"@ItemType":"Dimension","@DataMember":"addca.date","@DefaultId":"DataItem0","@DateTimeGroupInterval":"DayMonthYear"}],"range":["2025-01-01T08:24:37.000","2025-08-31T20:40:20.000"]}]}
    start_dt = mw.crmStart_dateedit.text()
    end_dt = mw.crmEnd_dateedit.text()
    #print(f"date {start_dt} - {end_dt}")
    parameter_2['Filter'][0]['range'] = f"['{start_dt}T00:00:00.000','{end_dt}T00:00:00.000']"
    
    query_final = str(parameter_2).replace(' ','')
    query_final = query_final.replace('\'','"')
    query_final = query_final.replace('"["','["')
    query_final = query_final.replace('"]"','"]')
    #print(query_final)
    encoded_query = urllib.parse.quote(query_final)
    # Make requests using the session
    session = requests.Session()
    #beack_cookie = cke + "; G_ENABLED_IDPS=google; _ga=GA1.2.2108095877.1755447542; _gid=GA1.2.1089913653.1755447542; _ga_YQ5GNLNM1N=GS2.2.s1755447543$o1$g1$t1755448285$j60$l0$h0; _gat=1; _ga_Q628CGYYW1=GS2.2.s1757697660$o1$g0$t1757697660$j60$l0$h0"
    beack_cookie = cke + "; G_ENABLED_IDPS=google; _ga=GA1.2.130067896.1744805028; _gid=GA1.2.1380914558.1757927855; _ga_Q628CGYYW1=GS2.2.s1757934471$o9$g0$t1757934471$j60$l0$h0; _gat=1; _ga_YQ5GNLNM1N=GS2.2.s1757938687$o41$g1$t1757938711$j36$l0$h0"
    stage2_headers["Cookie"] = beack_cookie
    session.headers.update(stage2_headers)

    bw_page3 = session.get(nUrl2)
    print(f"Final Data URL Status:{bw_page3.status_code}")
    mw.infotextcrm_lable.setText(f"Final Data URL Status:{bw_page3.status_code}")
    tmp_url = bw_page3.content.decode('utf-8')
    tmp_url = tmp_url.split("src=")
    tmp_url = tmp_url[1].split("\"")
    final_url = tmp_url[1]
    response = requests.request("GET", final_url, headers=stage3_headers)
    print(f"Request Status:{response.status_code}")
    mw.infotextcrm_lable.setText(f"Final Data URL Status:{bw_page3.status_code}")
    impData = response.content.decode('utf-8')
    impData = impData.split("dashboardSettings = ")
    impData = impData[1].split(";")
    final_dict = impData[0]
    TokenGuid = final_dict.split(',')[0].split("\"")[3]
    DashboardId = final_dict.split(',')[2].split("\"")[3]
    DataStorageKey = final_dict.split(',')[4].split("\"")[3]

    stage4_headers["api-token"] = TokenGuid
    stage4_headers["data-storage-key"] = DataStorageKey
    stage4_headers["referer"] = final_url
    print (f"TokenGuid: {TokenGuid}\nDataStorageKey: {DataStorageKey}\nDashboardId: {DashboardId}")
    mw.infotextcrm_lable.setText(f"DataStorageKey: {DataStorageKey}")
    '''
    for item in pd_name:
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        try:
            response = requests.request("GET", final_url, headers=stage4_headers)
            print(f"-------------------------- {item} ---------------------------------------")
            print(response.text)
            print("--------------------------------------------------------------------------")
            time.sleep(1)
        except:
            print(f"requests error in : {item}")
    
    '''
    try:
    #--------------------------------------------------------------------------------------------------------
        item = "gridDashboardItem3"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        dateList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']	# print(data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0'])
        storeList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1']	# print(data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1'])
        cardList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem6']
        tranList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem2']
        descList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem8']
        typeList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem5']
        barcodeList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem3']

        dateDict = {i: dateList[i] for i in range(0, len(dateList))}
        storeDict = {i: storeList[i] for i in range(0, len(storeList))}
        cardDict = {i: cardList[i] for i in range(0, len(cardList))}
        tranDict = {i: tranList[i] for i in range(0, len(tranList))}
        descDict = {i: descList[i] for i in range(0, len(descList))}
        typeDict = {i: typeList[i] for i in range(0, len(typeList))}
        barcodeDict = {i: barcodeList[i] for i in range(0, len(barcodeList))}

        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            x = tmpList
            z = valList.get(tmpList)
            a = x.replace('[','')
            b = a.replace(']','')
            dLine = b.split(',')
            detail_sale_data = detail_sale_data + f"{dateDict.get(int(dLine[0]))}, {storeDict.get(int(dLine[1]))}, {cardDict.get(int(dLine[2]))}, {tranDict.get(int(dLine[3]))}, {descDict.get(int(dLine[4]))}, {typeDict.get(int(dLine[5]))}, {barcodeDict.get(int(dLine[6]))}, {z.get('0')}, {z.get('1')}\n"
        
        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(detail_sale_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        
        item = "gridDashboardItem7"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = gridDashboardItem7_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']
        itemDict = {i: itemList[i] for i in range(0, len(itemList))}

        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            write_data = write_data + f"{itemDict.get(i)}, {z.get('0')}, {z.get('1')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "gridDashboardItem6"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = gridDashboardItem6_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']
        itemDict = {i: itemList[i] for i in range(0, len(itemList))}

        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            write_data = write_data + f"{itemDict.get(i)}, {z.get('0')}, {z.get('1')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
        
    #--------------------------------------------------------------------------------------------------------
        item = "chartDashboardItem2"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = chartDashboardItem2_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1']
        itemDict = {i: itemList[i] for i in range(0, len(itemList))}

        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            write_data = write_data + f"{itemDict.get(i)}, {z.get('0')}, {z.get('1')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "chartDashboardItem1"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = chartDashboardItem1_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList1 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']
        itemDict1 = {i: itemList1[i] for i in range(0, len(itemList1))}
        itemList2 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem2']
        itemDict2 = {i: itemList2[i] for i in range(0, len(itemList2))}
        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            a = tmpList.replace('[','')
            b = a.replace(']','')
            dLine = b.split(',')
            #print(f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}, {z.get('1')}")
            write_data = write_data + f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}, {z.get('1')}\n"


        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "pieDashboardItem1"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = pieDashboardItem1_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList1 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']
        itemDict1 = {i: itemList1[i] for i in range(0, len(itemList1))}
        itemList2 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem2']
        itemDict2 = {i: itemList2[i] for i in range(0, len(itemList2))}
        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            a = tmpList.replace('[','')
            b = a.replace(']','')
            dLine = b.split(',')
            #print(f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}, {z.get('1')}")
            write_data = write_data + f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "pieDashboardItem2"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = pieDashboardItem2_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList1 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']
        itemDict1 = {i: itemList1[i] for i in range(0, len(itemList1))}
        itemList2 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1']
        itemDict2 = {i: itemList2[i] for i in range(0, len(itemList2))}
        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']
        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            a = tmpList.replace('[','')
            b = a.replace(']','')
            dLine = b.split(',')
            #print(f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}, {z.get('1')}")
            write_data = write_data + f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "gridDashboardItem5"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = gridDashboardItem5_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList1 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem0']
        itemDict1 = {i: itemList1[i] for i in range(0, len(itemList1))}
        itemList2 = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1']
        itemDict2 = {i: itemList2[i] for i in range(0, len(itemList2))}
        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']
        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            a = tmpList.replace('[','')
            b = a.replace(']','')
            dLine = b.split(',')
            #print(f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}, {z.get('1')}")
            write_data = write_data + f"{itemDict1.get(int(dLine[0]))}, {itemDict2.get(int(dLine[1]))}, {z.get('0')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "pieDashboardItem6"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = pieDashboardItem6_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1']
        itemDict = {i: itemList[i] for i in range(0, len(itemList))}

        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            #print(f"{itemDict.get(i)}, {z.get('1')}, {z.get('0')}")
            write_data = write_data + f"{itemDict.get(i)}, {z.get('0')}, {z.get('1')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
        item = "pieDashboardItem5"
        page1 = f"https://www.biwee.fr/apiDashboardDesigner/data?dashboardId={DashboardId}&itemId={item}"
        final_url = f"{page1}&query={encoded_query}"
        write_data = pieDashboardItem5_data
        response = requests.request("GET", final_url, headers=stage4_headers)
        print(response.text)
        data = json.loads(response.text)
        reportName = data['CaptionViewModel']['Caption']
        itemList = data['ItemData']['DataStorageDTO']['EncodeMaps']['DataItem1']
        itemDict = {i: itemList[i] for i in range(0, len(itemList))}
        dataList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data'].keys()
        valList = data['ItemData']['DataStorageDTO']['Slices'][0]['Data']

        for i, tmpList in enumerate(dataList):
            z = valList.get(tmpList)
            write_data = write_data + f"{itemDict.get(i)}, {z.get('0')}\n"

        with open(os.path.join(mw.output_folder,f"{reportName}.csv"), "w") as csv_file:
            csv_file.write(write_data)
        
        time.sleep(1)
    #--------------------------------------------------------------------------------------------------------
    except Exception as e:
        print(f"requests error in : {item}, {type(e).__name__}")
        mw.infotextcrm_lable.setText(f"requests error in : {item}")

    print("All Done...")
    mw.infotextcrm_lable.setText(f"All Done...")
    return "Done."

def CRMGetToken(mw, progress_callback):
    all_text = f"CRMGetToken\n"
    progress_callback.emit(all_text)
    login_url = mw.crmUrl_lineedit.text()
    nUrl0 = "https://asp.adelya.com/loyaltyoperator/clients/specificContentWrapper.jsp?title=Statistiques%20YR%20UAE&goto=/AdelyaClientSpe/biwee/dashboards.jsp&ajax=true"
    nUrl2 = "https://asp.adelya.com/AdelyaClientSpe/biwee/dashboard.jsp?guid=485f9013-b78c-48ae-b129-b2501a166ad1"
    
    # Login ID and Password
    user_id = mw.crmUserID_lineedit.text()
    password = mw.crmPassword_lineedit.text()
    
    # run Chrome in headless mode
    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--headless")
    driver = webdriver.Edge(options=options)
    print("loggin: asp.adelya.com")
    mw.infotextcrm_lable.setText(r"loggin: asp.adelya.com")
    driver.get(login_url)
    driver.implicitly_wait(30)
    driver.maximize_window()
    eleLogin = driver.find_element(By.ID, "login")
    eleLogin.send_keys(user_id)
    elePassword = driver.find_element(By.ID, "password")
    elePassword.send_keys(password)
    driver.find_element(By.ID, "btn_connect").click()
    time.sleep(1)
    print("loggin successful")
    mw.infotextcrm_lable.setText(r"loggin successful")
    driver.get(nUrl0)
    time.sleep(1)
    driver.get(nUrl2)
    time.sleep(0.5)
    step_2_cookies = driver.get_cookies()
    j_session_id = None
    j_podks = None
    for cookie in step_2_cookies:
        if cookie['name'] == 'PODIDAKS':
            j_podks = cookie['value']
            #print(cookie)

        if cookie['name'] == 'JSESSIONID':
            j_session_id = cookie['value']
            
    cke = ""
    # Print the JSESSIONID value
    if j_session_id:
        print(f"PODIDAKS={j_podks}; JSESSIONID={j_session_id}")
        cke = f"PODIDAKS={j_podks}; JSESSIONID={j_session_id}"
        mw.infotextcrm_lable.setText(r"Done")
    else:
        print("JSESSIONID cookie not found.")
        mw.infotextcrm_lable.setText(r"JSESSIONID cookie not found.")

    time.sleep(0.5)
    driver.quit()
    mw.crmToken_lineedit.setText(cke)
    return "Done."