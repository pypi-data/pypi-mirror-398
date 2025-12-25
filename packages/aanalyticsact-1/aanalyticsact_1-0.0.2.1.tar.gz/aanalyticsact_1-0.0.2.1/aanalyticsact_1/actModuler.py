# Created by Sunkyeong Lee
# Inquiry : sunkyeong.lee@concentrix.com / sunkyong9768@gmail.com
# Updated & Managed by Youngkwang Cho
# Inquiry : youngkwang.Cho@concentrix.com / ykc124@naver.com
# encoding, create_engine(),apply & map, limit function
# 2nd Breakdown w/ total value, jsonToDB + refinedFrame to refinedFrame1
# EmptyDataError
# 251212 worker_refine_common 추가, RetryableServerError() 추가

import aanalytics2 as api2
import aanalyticsactauth as auth
import json
from datetime import datetime, timedelta
from copy import deepcopy
from sqlalchemy import create_engine
import os
import re
import time

from sqlalchemy import pool   ###YK
from sqlalchemy.pool import NullPool ###YK
import pandas as pd ###YK

class RetryableServerError(Exception):
    pass

class EmptyDataError(Exception):
    pass

# initator
def dataInitiator():
    api2.importConfigFile(os.path.join(auth.auth, 'aanalyticsact_auth.json'))
    logger = api2.Login()
    logger.connector.config

def dataReportSuites():
    cid = "samsun0"
    ags = api2.Analytics(cid)
    ags.header
    rsids = ags.getReportSuites()
    print(rsids)

# data retrieving function
def dataretriever_data(jsonFile):
    cid = "samsun0"
    ags = api2.Analytics(cid)
    ags.header
    myreport = ags.getReport(jsonFile, limit=1000000, n_results='inf')
    if myreport['data'].empty: 
        raise EmptyDataError
    return myreport['data']


def dataretriever_data_breakdown(jsonFile):
    cid = "samsun0"
    ags = api2.Analytics(cid)
    ags.header
    myreport1 = ags.getReport(jsonFile, limit=1000000, n_results='inf',item_id=True)
    if myreport1['data'].empty: 
        raise EmptyDataError
    data_report = myreport1['data']

    return data_report


def exportToCSV(dataSet, fileName):
    dataSet.to_csv(fileName, sep=',', index=False)


def returnRsID(jsonFile):
    with open(jsonFile, 'r', encoding='UTF-8') as bla:
        json_data = json.loads(bla.read())
    json_data.pop("capacityMetadata")
    rsID = json_data['rsid']

    return rsID


def EndDateCalculation(startDate, endDate):
    startDate = str(startDate)
    endDate = datetime.strptime(endDate, '%Y-%m-%d').date()
    endDate += timedelta(days=1)
    endDate = str(endDate)

    return startDate, endDate


def timeChanger(time_obj, start):
    if start == True:
        return str('T' + time_obj + ':00.000/')
    else:
        time_obj = datetime.strptime(time_obj, "%H:%M")
        time_obj += timedelta(minutes=1)
        return str('T' + str(time_obj.strftime("%H:%M"))+ ':00.000')
    

def jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour):

    startDate = EndDateCalculation(startDate, endDate)[0]
    endDate = EndDateCalculation(startDate, endDate)[1]

    with open(jsonFile, 'r', encoding='UTF-8') as bla:
        json_data = json.load(bla)
    json_data.pop("capacityMetadata")

    globalFilterElement = json_data['globalFilters']
    if start_hour == "00:00" and end_hour == "00:00":
        tobeDate = str(startDate + "T00:00:00.000/" + endDate + "T00:00:00.000")
    else :
        tobeDate = str(startDate + timeChanger(start_hour, True) + endDate + timeChanger(end_hour, False))
        
    for i in range(len(globalFilterElement)):
        globalFilterElement[i]['dateRange'] = tobeDate

    json_data['globalFilters'] = globalFilterElement
    
    return json_data

def addStartEndDateColumn(startDate, endDate, rowNum):
    startDateList = []
    endDateList = []

    for i in range(rowNum):
        startDateList.append(startDate)
        endDateList.append(endDate)

    return startDateList, endDateList

def checkSiteCode(dimension):
    if (dimension == "variables/prop1" or dimension == "variables/evar1" or dimension == "variables/entryprop1"):
        return True

    else:
        return False

# 1st Level data Caller
def refinedFrame(startDate, endDate, period, jsonFile, epp, if_site_code, site_code_rs, start_hour, end_hour):
    dataInitiator()
    dateChange = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    dataFrame = dataretriever_data(dateChange)

    if dateChange['rsid'] != "sssamsung4mstglobal":
        columnList = []
        for i in range(dataFrame.shape[1]):
            columnList.append(i)

        dataFrame.columns = columnList

        if site_code_rs == True:
            dataFrame = dataFrame.drop(0,axis =1)

        if dateChange['rsid'] == "sssamsungnewus":
            dataFrame.insert(0, "site_code", "us", True)

        else:
            rsName = dateChange['rsid'].split('4')
            if "epp" in rsName[-1]:
                dataFrame.insert(0, "site_code", rsName[-1].replace('epp', ''), True)
                epp = "Y"
            else:
                dataFrame.insert(0, "site_code", rsName[-1], True)

    if (if_site_code == True or site_code_rs == True):
        dataFrame.insert(1, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame.insert(2, "start_date", startDate, True)
            dataFrame.insert(3, "end_date", endDate, True)
        else :
            dataFrame.insert(2, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame.insert(3, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)     
        dataFrame.insert(4, "is_epp", epp, True)
    else:
        if dateChange['rsid'] == "sssamsung4mstglobal":
            dataFrame.insert(0, "site_code", "MST", True)
        dataFrame.insert(2, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame.insert(3, "start_date", startDate, True)
            dataFrame.insert(4, "end_date", endDate, True)        
        else :
            dataFrame.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
        dataFrame.insert(5, "is_epp", epp, True)

    return dataFrame  

# updated 220527. smb site code added
# updated 221202. my bday! :D smb site code added (10.31 open)
# updated 240813 app site code added (636 site code)
# updated 250204 site code + site code app (103+103 site code)

def filterSiteCode(dataframe, site_code):
    if site_code != "":
        return dataframe.loc[dataframe['site_code'].isin(site_code)]
    else :
       return dataframe.loc[dataframe['site_code'].isin(["ae","ae_ar","africa_en","africa_fr","africa_pt","al","ar","at","au","az","ba","bd","be","be_fr","bg","bh","bh_ar","br","ca","ca_fr","ch","ch_fr","cl","cn","co","cz","de","dk","ee","eg","eg_en","es","fi","fr","ge","gr","hk","hk_en","hr","hu","id","ie","il","in","iq_ar","iq_ku","iran","it","jo","jo_ar","jp","kw","kw_ar","kz_kz","kz_ru","latin","latin_en","lb","levant","levant_ar","lt","lv","ma","mk","mm","mn","mx","my","n_africa","nl","no","nz","om","om_ar","pe","ph","pk","pl","ps","pt","py","qa","qa_ar","ro","rs","ru","sa","sa_en","se","sec","sg","si","sk","th","tr","tw","ua","uk","uy","uz_ru","uz_uz","vn","za",
"ae-app","ae_ar-app","africa_en-app","africa_fr-app","africa_pt-app","al-app","ar-app","at-app","au-app","az-app","ba-app","bd-app","be-app","be_fr-app","bg-app","bh-app","bh_ar-app","br-app","ca-app","ca_fr-app","ch-app","ch_fr-app","cl-app","cn-app","co-app","cz-app","de-app","dk-app","ee-app","eg-app","eg_en-app","es-app","fi-app","fr-app","ge-app","gr-app","hk-app","hk_en-app","hr-app","hu-app","id-app","ie-app","il-app","in-app","iq_ar-app","iq_ku-app","iran-app","it-app","jo-app","jo_ar-app","jp-app","kw-app","kw_ar-app","kz_kz-app","kz_ru-app","latin-app","latin_en-app","lb-app","levant-app","levant_ar-app","lt-app","lv-app","ma-app","mk-app","mm-app","mn-app","mx-app","my-app","n_africa-app","nl-app","no-app","nz-app","om-app","om_ar-app","pe-app","ph-app","pk-app","pl-app","ps-app","pt-app","py-app","qa-app","qa_ar-app","ro-app","rs-app","ru-app","sa-app","sa_en-app","se-app","sec-app","sg-app","si-app","sk-app","th-app","tr-app","tw-app","ua-app","uk-app","uy-app","uz_ru-app","uz_uz-app","vn-app","za-app"
])] 


# updated 210907. added site_code_rs for us integration(us has no site code)
# updated 240813 extra1 added
def jsonToDb(startDate, endDate, period, jsonLocation, tbColumn, dbTableName, epp, if_site_code, site_code_rs, limit, extra, extra1, start_hour, end_hour, site_code):
    df = refinedFrame(startDate, endDate, period, jsonLocation, epp, if_site_code, site_code_rs, start_hour, end_hour)
    df.columns = tbColumn
    if extra != "":
        df.insert(5, "extra", extra, True)
    if extra1 != "":
        df.insert(6, "extra1", extra1, True)
    if limit == 0:
        df = df
    else:
        df = df.head(limit)

    if if_site_code == True:
        if returnRsID(jsonLocation) == "sssamsung4mstglobal":
            df = filterSiteCode(df, site_code)
 
    stackTodb(df, dbTableName)

def create_connection_pool():   ###YK
    db_connection_str = 'mysql+pymysql://root:12345@127.0.0.1:3307/act?charset=utf8mb4'
    pool_size = 20  
    max_overflow = 10  
    return create_engine(db_connection_str, poolclass=pool.QueuePool, pool_size=pool_size, max_overflow=max_overflow)

def stackTodb(dataFrame, dbTableName):  ###YK
 #   print(dataFrame)
    # UNICODE 전처리
    dataFrame = unicodeCompile_df(dataFrame)
    db_connection = create_connection_pool()
    with db_connection.connect() as conn:
        dataFrame.to_sql(name=dbTableName, con=conn, if_exists='append', index=False)
    db_connection.dispose()
    print("finished")

def stackTodb_RB(dataFrame, dbTableName):  ###YK
    # print(dataFrame)
    # UNICODE 전처리
    dataFrame = unicodeCompile_df(dataFrame)
    db_connection = create_connection_pool()
    with db_connection.connect() as conn:
        dataFrame.to_sql(name=dbTableName, con=conn, if_exists='append', index=False)
    db_connection.dispose()
    print("finished")
   
   
""" MST breakdown """

# breakdown itemID
def ChangeItemID(itemID, breakdownJson):
    temp_breakdownJson = deepcopy(breakdownJson)
    before_temp = temp_breakdownJson['metricContainer']['metricFilters']

    # change date > call using itemID iteration
    after_temp = deepcopy(before_temp)
    for i in range(len(after_temp)):
        if "itemId" in after_temp[i]:
            after_temp[i]["itemId"] = itemID
        else:
            continue

    temp_breakdownJson['metricContainer']['metricFilters'] = after_temp

    return temp_breakdownJson


def readJson(jsonFile):
    with open(jsonFile, 'r', encoding='UTF-8') as bla:
        json_data = json.loads(bla.read())
    json_data.pop("capacityMetadata")
    return json_data
        

def returnItemID(startDate, endDate, jsonItemID, start_hour, end_hour, site_code):
    jsonFile = deepcopy(jsonItemID)
    itemIDjson = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)

    dataInitiator()

    itemIDdf = dataretriever_data_breakdown(itemIDjson)

    columnList = list(map(str, range(itemIDdf.shape[1])))   

    columnList[0] = 'site_code'
    columnList[-1] = 'item_id'

    itemIDdf.columns = columnList

    if (itemIDjson["dimension"] == "variables/prop1" or itemIDjson["dimension"] == "variables/evar1" or itemIDjson["dimension"] == "variables/entryprop1"):
        itemIDdfFiltered = filterSiteCode(itemIDdf, site_code)
        itemIDlist = itemIDdfFiltered[['site_code', 'item_id']].values.tolist()        

    else:
        itemIDlist = itemIDdf[['site_code', 'item_id']].values.tolist()

    return itemIDlist

def returnItemID_rs(jsonItemID):
    dataInitiator()

    itemIDdf = dataretriever_data_breakdown(jsonItemID)

    columnList = list(map(str, range(itemIDdf.shape[1])))   

    columnList[0] = 'site_code'
    columnList[-1] = 'item_id'

    itemIDdf.columns = columnList
    itemIDlist = itemIDdf[['site_code', 'item_id']].values.tolist()

    return itemIDlist

#emoji eliminator
def unicodeCompile_df(df):
    only_BMP_pattern = re.compile("["
                                  u"\U00010000-\U0010FFFF"  # out of BMP characters 
                                  "]+", flags=re.UNICODE)

    def remove_non_bmp(text):
        if isinstance(text, str):
            return only_BMP_pattern.sub(r'', text) # only BMP characters
        else:
            return text  # 문자열이 아닌 경우 그대로 반환

    return df.apply(lambda col: col.map(remove_non_bmp))#df.apply(remove_non_bmp)

# Save as dictionary format return in tuple
def ReturnJsonchanged(startDate, endDate, jsonFile, jsonFilebreakdown, start_hour, end_hour, site_code):
    itemIDList = returnItemID(startDate, endDate, jsonFile, start_hour, end_hour, site_code)

    itemIDdict = {}
    for i in range(len(itemIDList)):
        jsonbreakdown = jsonDateChange(startDate, endDate, jsonFilebreakdown, start_hour, end_hour)
        itemIDdict[itemIDList[i][0]] = ChangeItemID(itemIDList[i][1], jsonbreakdown)
    
    itemIDdict = list(zip(itemIDdict.keys(), itemIDdict.values()))
    
    return itemIDdict

def StackbreakValue(startDate, endDate, period, jsonFile, jsonFilebreakdown, tbColumn, dbTableName, epp, limit1,limit2, extra, extra1, start_hour, end_hour, site_code):
    if returnRsID(jsonFile) == "sssamsung4mstglobal":
        itemIDdict = ReturnJsonchanged(startDate, endDate, jsonFile, jsonFilebreakdown, start_hour, end_hour, site_code)

        # iterable = list(map(int, range(len(itemIDdict))))

        # pool = multiprocessing.Pool(4)
        # func = partial(mstbreakDown, itemIDdict, startDate, endDate, period, tbColumn, dbTableName, epp, limit)
        # pool.map(func, iterable)
        # pool.close()
        # pool.join()

        if limit1 != 0 :
            itemIDdict = itemIDdict[:limit1]
        for i in range(len(itemIDdict)):
            try :
                dataFrame = dataretriever_data(itemIDdict[i][1])

                if limit2 == 0:
                    dataFrame2 = dataFrame
                else:
                    dataFrame2 = dataFrame.head(limit2)

                dataFrame2.insert(0, "site_code", itemIDdict[i][0], True)
                dataFrame2.insert(2, "period", period, True)
                if start_hour == "00:00" and end_hour == "00:00":
                    dataFrame2.insert(3, "start_date", startDate, True)
                    dataFrame2.insert(4, "end_date", endDate, True)
                else :
                    dataFrame2.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
                    dataFrame2.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
                dataFrame2.insert(5, "is_us_epp", epp, True)

                dataFrame2.columns = tbColumn
                if extra != "":
                    dataFrame2.insert(6, "extra", extra, True)
                if extra1 != "":
                    dataFrame2.insert(7, "extra1", extra1, True)
                stackTodb(dataFrame2, dbTableName)
            except EmptyDataError : 
           #     print(itemIDdict[i][0])
                continue
    else:
        dataInitiator()
        dateChange = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
        dataFrame = dataretriever_data(dateChange)

        dataFrame.columns = list(map(int, range(dataFrame.shape[1])))
        
        if limit2 == 0:
            dataFrame2 = dataFrame
        else:
            dataFrame2 = dataFrame.head(limit2)

        if returnRsID(jsonFile) == "sssamsungnewus":
            dataFrame2.insert(0, "site_code", "us", True)
        else:
            rsName = dateChange['rsid'].split('4')
            dataFrame2.insert(0, "site_code", rsName[-1], True)   

        dataFrame2.insert(2, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame2.insert(3, "start_date", startDate, True)
            dataFrame2.insert(4, "end_date", endDate, True)
        else :
            dataFrame2.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame2.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
        dataFrame2.insert(5, "is_us_epp", epp, True)

        dataFrame2.columns = tbColumn
        if extra != "":
           dataFrame2.insert(6, "extra", extra, True)
        if extra1 != "":
           dataFrame2.insert(7, "extra1", extra1, True)

        stackTodb(dataFrame2, dbTableName)

"""Return after RS Name changed"""

def rsIDchange(jsonFile, rsID):
    temp_simple = deepcopy(jsonFile)
    temp_simple['rsid'] = rsID

    return temp_simple

def refineRsIDChange(startDate, endDate, jsonFile, rsList, period, tbColumn, dbTableName, epp, limit, extra, extra1, start_hour, end_hour):
    datechanged = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    rschanged = rsIDchange(datechanged, rsList[1])

    dataInitiator()
    dataFrame1 = dataretriever_data(rschanged)
    if limit == 0 :
        dataFrame=dataFrame1
    else :
        dataFrame=dataFrame1.head(limit)

    columnList = []
    for i in range(dataFrame.shape[1]):
        columnList.append(i)

    dataFrame.columns = columnList

    dataFrame.insert(0, "site_code", rsList[0], True)
    dataFrame.insert(2, "period", period, True)
    if start_hour == "00:00" and end_hour == "00:00":
        dataFrame.insert(3, "start_date", startDate, True)
        dataFrame.insert(4, "end_date", endDate, True)
    else :
        dataFrame.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
        dataFrame.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)

    if epp == True:
        dataFrame.insert(5, "is_epp", "Y", True)
    else:
        dataFrame.insert(5, "is_epp", "N", True)

    if (rsList[1] == "sssamsungnewus" or rsList[1] == "sssamsung4sec"):
        dataFrame.insert(6, "is_epp_integ", "Y", True)
    else:
        dataFrame.insert(6, "is_epp_integ", "N", True)
            
    dataFrame.columns = tbColumn
    if extra != "":
        dataFrame.insert(7, "extra", extra, True)
    if extra1 != "":
        dataFrame.insert(8, "extra1", extra1, True)
    stackTodb(dataFrame, dbTableName)
    print(rsList[1],startDate,endDate)
    
def secondCaller1(startDate, endDate, jsonFile, jsonFilebreakdown, rsList, limit, period, tbColumn, dbTableName, epp, extra="", extra1="", start_hour="00:00", end_hour="00:00"):
    dateChanged_json = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    dateChanged_bd_json = jsonDateChange(startDate, endDate, jsonFilebreakdown, start_hour, end_hour)
    
    rsChanged_json = rsIDchange(dateChanged_json, rsList[1])
    rsChanged_json_bd = rsIDchange(dateChanged_bd_json, rsList[1])

    itemIDList = returnItemID_rs(rsChanged_json)

    itemIDdict = {}
    for i in range(len(itemIDList)):
        itemIDdict[itemIDList[i][0]] = ChangeItemID(itemIDList[i][1], rsChanged_json_bd)
    
    itemIDdict = list(zip(itemIDdict.keys(), itemIDdict.values()))

    for i in range(len(itemIDdict)):
        dataFrame = dataretriever_data(itemIDdict[i][1])
        
        if limit == 0:
            dataFrame2 = dataFrame
        else:
            dataFrame2 = dataFrame.head(limit)

        dataFrame2.insert(0, "site_code", rsList[0], True)
        dataFrame2.insert(1, "dimension", itemIDdict[i][0], True)
        dataFrame2.insert(3, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame2.insert(4, "start_date", startDate, True)
            dataFrame2.insert(5, "end_date", endDate, True)
        else :
            dataFrame2.insert(4, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame2.insert(5, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
        dataFrame2.insert(6, "epp", epp, True)
        
        if extra != "":
            dataFrame2.insert(7, "extra", extra, True)
        if extra1 != "":
            dataFrame2.insert(8, "extra1", extra1, True)
        dataFrame2.columns = tbColumn
        stackTodb(dataFrame2, dbTableName)

def secondCaller(startDate, endDate, jsonFile, jsonFilebreakdown, rsList, period, tbColumn, dbTableName, epp, limit1, limit2, extra="", extra1="", start_hour="00:00", end_hour="00:00"):
    dateChanged_json = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    dateChanged_bd_json = jsonDateChange(startDate, endDate, jsonFilebreakdown, start_hour, end_hour)
    
    rsChanged_json = rsIDchange(dateChanged_json, rsList[1])
    rsChanged_json_bd = rsIDchange(dateChanged_bd_json, rsList[1])

    itemIDList = returnItemID_rs(rsChanged_json)
    itemIDdict = {}
    for i in range(len(itemIDList)):
        itemIDdict[itemIDList[i][0]] = ChangeItemID(itemIDList[i][1], rsChanged_json_bd)
    
    itemIDdict = list(zip(itemIDdict.keys(), itemIDdict.values()))

    if limit1==0:
        lenItemID = len(itemIDdict)
    else :
        lenItemID = min(len(itemIDdict),limit1)

    for i in range(lenItemID):
        dataFrame = dataretriever_data(itemIDdict[i][1])
        
        if limit2 == 0:
            dataFrame2 = dataFrame
        else:
            dataFrame2 = dataFrame.head(limit2)

        dataFrame2.insert(0, "site_code", rsList[0], True)
        dataFrame2.insert(1, "dimension", itemIDdict[i][0], True)
        dataFrame2.insert(3, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame2.insert(4, "start_date", startDate, True)
            dataFrame2.insert(5, "end_date", endDate, True)
        else :
            dataFrame2.insert(4, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame2.insert(5, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
        dataFrame2.insert(6, "epp", epp, True)
        
        if extra != "":
            dataFrame2.insert(7, "extra", extra, True)
        if extra1 != "":
            dataFrame2.insert(8, "extra1", extra1, True)
        dataFrame2.columns = tbColumn
        stackTodb(dataFrame2, dbTableName)

def refineRsIDChangeRB(startDate, endDate, jsonFile, rsList, period, tbColumn, dbTableName, epp, limit, Biz_type, Device_type, Division, Category, site_code_ae, start_hour, end_hour):
    datechanged = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    rschanged = rsIDchange(datechanged, rsList[1])

    dataInitiator()
    dataFrame1 = dataretriever_data(rschanged)
    if limit == 0 :
        dataFrame=dataFrame1
    else :
        dataFrame=dataFrame1.head(limit)

    columnList = []
    for i in range(dataFrame.shape[1]):
        columnList.append(i)

    dataFrame.columns = columnList

    if site_code_ae != "" :
        dataFrame.insert(0, "site_code", site_code_ae, True)
    else :
        dataFrame.insert(0, "site_code", rsList[0], True)

    dataFrame.insert(1, "RS ID", rsList[1], True)
    
    dataFrame.insert(2, "Biz_type", Biz_type, True)
    dataFrame.insert(3, "Division", Division, True)
    dataFrame.insert(4, "Category", Category,True)
    dataFrame.insert(5, "Device_type", Device_type, True)
    dataFrame.insert(6, "Date", startDate, True)
    dataFrame.columns = tbColumn
    print(rsList[1],startDate,Biz_type, Device_type, Division, Category)
    stackTodb(dataFrame, dbTableName)


##### UPDATE
def refineRsIDChangeTotal(startDate, endDate, jsonFile, rsList, period, tbColumn, dbTableName, epp, limit, extra, extra1, start_hour, end_hour):
    datechanged = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    rschanged = rsIDchange(datechanged, rsList[1])

    dataInitiator()
    dataFrame1 = dataretriever_data(rschanged)
    if limit == 0 :
        dataFrame=dataFrame1
    else :
        dataFrame=dataFrame1.head(limit)

    columnList = []
    for i in range(dataFrame.shape[1]):
        columnList.append(i)

#    dataFrame.columns = columnList

    dataFrame.insert(0, "site_code", rsList[0], True)
    dataFrame.insert(2, "breakdown", "Total", True)
    dataFrame.insert(3, "period", period, True)
    if start_hour == "00:00" and end_hour == "00:00":
        dataFrame.insert(4, "start_date", startDate, True)
        dataFrame.insert(5, "end_date", endDate, True)
    else :
        dataFrame.insert(4, "start_date", "{0} {1}".format(startDate, start_hour), True)
        dataFrame.insert(5, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)

    if epp == True:
        dataFrame.insert(6, "epp", "Y", True)
    else:
        dataFrame.insert(6, "epp", "N", True)

    if extra != "":
        dataFrame.insert(7, "extra", extra, True)
    if extra1 != "":
        dataFrame.insert(8, "extra1", extra1, True)
    dataFrame.columns = tbColumn

    stackTodb(dataFrame, dbTableName)

def refinedFrame1(startDate, endDate, period, jsonFile,  tbColumn, dbTableName, epp, if_site_code, site_code_rs,  limit, extra, extra1,start_hour, end_hour, site_code):
    dataInitiator()
    dateChange = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    dataFrame = dataretriever_data(dateChange)

    if dateChange['rsid'] != "sssamsung4mstglobal":
        columnList = []
        for i in range(dataFrame.shape[1]):
            columnList.append(i)

        dataFrame.columns = columnList

        if site_code_rs == True:
            dataFrame = dataFrame.drop(0,axis =1)

        if dateChange['rsid'] == "sssamsungnewus":
            dataFrame.insert(0, "site_code", "us", True)

        else:
            rsName = dateChange['rsid'].split('4')
            if "epp" in rsName[-1]:
                dataFrame.insert(0, "site_code", rsName[-1].replace('epp', ''), True)
                epp = "Y"
            else:
                dataFrame.insert(0, "site_code", rsName[-1], True)

    if (if_site_code == True or site_code_rs == True):
        dataFrame.insert(1, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame.insert(2, "start_date", startDate, True)
            dataFrame.insert(3, "end_date", endDate, True)
        else :
            dataFrame.insert(2, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame.insert(3, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)     
        dataFrame.insert(4, "is_epp", epp, True)
    else:
        if dateChange['rsid'] == "sssamsung4mstglobal":
            dataFrame.insert(0, "site_code", "MST", True)
        dataFrame.insert(2, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame.insert(3, "start_date", startDate, True)
            dataFrame.insert(4, "end_date", endDate, True)        
        else :
            dataFrame.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
        dataFrame.insert(5, "is_epp", epp, True)

    dataFrame.columns = tbColumn
    if extra != "":
        dataFrame.insert(5, "extra", extra, True)
    if extra1 != "":
        dataFrame.insert(6, "extra1", extra1, True)

    if if_site_code == True:
        if returnRsID(jsonFile) == "sssamsung4mstglobal":
            dataFrame = filterSiteCode(dataFrame, site_code)
    if limit == 0:
        dataFrame = dataFrame
    else:
        dataFrame = dataFrame.head(limit)
    stackTodb(dataFrame, dbTableName)


def refinedFrameTotal(startDate, endDate, period, jsonFile,  tbColumn, dbTableName, epp, if_site_code, site_code_rs,  limit, extra, extra1, start_hour, end_hour, site_code):
    dataInitiator()
    dateChange = jsonDateChange(startDate, endDate, jsonFile, start_hour, end_hour)
    dataFrame = dataretriever_data(dateChange)

    if dateChange['rsid'] != "sssamsung4mstglobal":
        columnList = []
        for i in range(dataFrame.shape[1]):
            columnList.append(i)

        dataFrame.columns = columnList

        if site_code_rs == True:
            dataFrame = dataFrame.drop(0,axis =1)

        if dateChange['rsid'] == "sssamsungnewus":
            dataFrame.insert(0, "site_code", "us", True)

        else:
            rsName = dateChange['rsid'].split('4')
            if "epp" in rsName[-1]:
                dataFrame.insert(0, "site_code", rsName[-1].replace('epp', ''), True)
                epp = "Y"
            else:
                dataFrame.insert(0, "site_code", rsName[-1], True)

    if (if_site_code == True or site_code_rs == True):
        dataFrame.insert(1, "breakdown", "Total", True)
        dataFrame.insert(2, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame.insert(3, "start_date", startDate, True)
            dataFrame.insert(4, "end_date", endDate, True)
        else :
            dataFrame.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)     
        dataFrame.insert(5, "is_epp", epp, True)
    else:
        if dateChange['rsid'] == "sssamsung4mstglobal":
            dataFrame.insert(0, "site_code", "MST", True)
        dataFrame.insert(2, "period", period, True)
        if start_hour == "00:00" and end_hour == "00:00":
            dataFrame.insert(3, "start_date", startDate, True)
            dataFrame.insert(4, "end_date", endDate, True)        
        else :
            dataFrame.insert(3, "start_date", "{0} {1}".format(startDate, start_hour), True)
            dataFrame.insert(4, "end_date", "{0} {1}".format(EndDateCalculation("0", endDate)[1], end_hour), True)
        dataFrame.insert(5, "is_epp", epp, True)

    dataFrame.columns = tbColumn
    if extra != "":
        dataFrame.insert(6, "extra", extra, True)
    if extra1 != "":
        dataFrame.insert(7, "extra1", extra1, True)


    if if_site_code == True:
        if returnRsID(jsonFile) == "sssamsung4mstglobal":
            dataFrame = filterSiteCode(dataFrame, site_code)
    if limit == 0:
        dataFrame = dataFrame
    else:
        dataFrame = dataFrame.head(limit)
 
    stackTodb(dataFrame, dbTableName)

########### UPDATE
def worker_refine_RS(task):
    (startDate, endDate, jsonLocation, rs, period, tbColumn, dbTableName,
        epp, limit, extra, extra1, start_hour, end_hour, max_retries
     ) = task

    retry = 0
    while retry < max_retries:
        try:
            start = time.time()
            refineRsIDChange(startDate, endDate, jsonLocation, rs, period, tbColumn, dbTableName, epp, limit, extra, extra1, start_hour, end_hour)

            print("Time:", round(time.time() - start, 2), "sec")
            return

        except EmptyDataError:
            print("Empty:", rs, startDate, endDate)
            return
        except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError ,RetryableServerError):
            retry += 1
            continue

    print(f"[Retry Fail] {rs} - {startDate}")

def worker_refine_RB(task):
    (startDate, endDate, jsonLocation, rs, period, tbColumn, dbTableName, 
         epp, limit, Biz_type, Device_type, Division, Category, site_code_ae, start_hour, end_hour, max_retries
     ) = task

    retry = 0
    while retry < max_retries:
        try:
            start = time.time()
            refineRsIDChangeRB(startDate, endDate, jsonLocation, rs, period, tbColumn, dbTableName, epp, limit, Biz_type, Device_type, Division, Category, site_code_ae, start_hour, end_hour)
            
            print("Time:", round(time.time() - start, 2), "sec")
            return

        except EmptyDataError:
            print("Empty:", rs, startDate, endDate)
            return
        except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
            retry += 1
            continue

    print(f"[Retry Fail] {rs} - {startDate}")

def worker_refine_common(task):
    (startDate, endDate, jsonLocation, rs, period, tbColumn, dbTableName,
        epp, limit, extra, extra1, start_hour, end_hour, max_retries,
        mode  # "RB" or "RS"
    ) = task

    retry = 0
    while retry < max_retries:
        try:
            start = time.time()

            if mode == "RB":
                refineRsIDChangeRB(startDate, endDate, jsonLocation, rs,
                                   period, tbColumn, dbTableName, epp, limit,
                                   extra, extra1, "", start_hour, end_hour)

            else:  # mode == "RS"
                refineRsIDChange(startDate, endDate, jsonLocation, rs,
                                 period, tbColumn, dbTableName, epp, limit,
                                 extra, extra1, start_hour, end_hour)

            print("Time:", round(time.time() - start, 2), "sec")
            return

        except EmptyDataError:
            print("Empty:", rs, startDate, endDate)
            return
        except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
            retry += 1
            continue

    print(f"[Retry Fail] {rs} - {startDate}")
