# Created by Sunkyeong Lee
# Inquiry : sunkyeong.lee@concentrix.com / sunkyong9768@gmail.com
# Updated & Managed by Youngkwang Cho
# Inquiry : youngkwang.Cho@concentrix.com / ykc124@naver.com
# limit function and para order
# JsonToDB To refinedFrame1
# 20251212 retrieve_RB_parallel, retrieve_by_RS_parallel 추가

from copy import Error
# from actModuler import *
# from actRunner import *
from .actModuler import *
from .actRunner import *
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def retrieve_FirstLevel(start_date, end_date, period, jsonLocation, tbColumn, dbTableName, epp, site_code_rs, limit=0, extra = "", extra1 = "", start_hour="00:00", end_hour="00:00", site_code = "", max_retries = 5):
    if limit > 10000:
        raise Error("limit은 0 ~ 10000 사이 값으로 넣어주세요")

    dateCaller = dateGenerator(start_date, end_date, period)
    if_site_code = checkSiteCode(readJson(jsonLocation)["dimension"])
    
    tbColumn = tbColumnGenerator(tbColumn, if_site_code, False, False, site_code_rs)
    
    startDate = dateCaller[0]
    endDate = dateCaller[1]

    for i in range(len(startDate)):
        retry_count = 0
        while retry_count < max_retries:
            try:
                start = time.time()
                refinedFrame1(startDate[i], endDate[i], period, jsonLocation, tbColumn, dbTableName, epp, if_site_code, site_code_rs, limit, extra, extra1, start_hour, end_hour, site_code)
                break
            except EmptyDataError : 
            	print(startDate[i], endDate[i] )
            	break
            except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                retry_count += 1
                continue

   
            if retry_count == max_retries:
                print(f"Max retries {max_retries} reached. Moving to the next task.")
            else:
                continue  
        timeSec = round(time.time() - start, 2)
        print("Time took: ", timeSec, "sec")

def retrieve_SecondLevel(start_date, end_date, period, jsonLocation, jsonLocation_breakdown,tbColumn, dbTableName, epp, limit1=0,limit2=0, extra = "", extra1 = "", start_hour="00:00", end_hour="00:00", site_code="", max_retries = 5):
    dateCaller = dateGenerator(start_date, end_date, period)
    if_site_code = checkSiteCode(readJson(jsonLocation)["dimension"])

    if returnRsID(jsonLocation) == "sssamsungnewus":
        if_site_code = True

    site_code_rs = False
    tbColumn = tbColumnGenerator(tbColumn, if_site_code, True, False, site_code_rs)
    
    startDate = dateCaller[0]
    endDate = dateCaller[1]

    for i in range(len(startDate)):
        retry_count = 0
        while retry_count < max_retries:
            try:
                start = time.time()
                StackbreakValue(startDate[i], endDate[i], period, jsonLocation, jsonLocation_breakdown, tbColumn, dbTableName, epp, limit1, limit2, extra, extra1, start_hour, end_hour, site_code)
                break

            except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                retry_count += 1
                continue

            if retry_count == max_retries:
                print(f"Max retries {max_retries} reached. Moving to the next task.")
            else:
                continue  

        timeSec = round(time.time() - start, 2)
        print("Time took: ", timeSec, "sec")


def retrieve_by_RS(start_date, end_date, period, jsonLocation, rsInput, tbColumn, dbTableName, epp, limit=0, extra = "", extra1 = "",start_hour="00:00", end_hour="00:00", max_retries = 5):
    dateCaller = dateGenerator(start_date, end_date, period)
    site_code_rs = False
    tbColumn = tbColumnGenerator(tbColumn, False, False, True, site_code_rs)
    
    startDate = dateCaller[0]
    endDate = dateCaller[1]

    rsList = returnRsList(epp, rsInput)

    for j in range(len(rsList)):
        for i in range(len(startDate)):
            retry_count = 0
            while retry_count < max_retries:
                try:
                  start = time.time()
                  refineRsIDChange(startDate[i], endDate[i], jsonLocation, rsList[j], period, tbColumn, dbTableName, epp, limit, extra, extra1, start_hour, end_hour)
                  timeSec = round(time.time() - start, 2)
                  print("Time took: ", timeSec, "sec")
                  break

                except EmptyDataError:
                    print(rsList[j],startDate[i], endDate[i] )
                    break

                except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                    retry_count += 1
                    continue


            if retry_count == max_retries:
                print(f"Max retries {max_retries} reached. Moving to the next task.")
            else:
                continue  
    


def retrieve_by_RS_breakdown(startDate, endDate, period, jsonFile, jsonFilebreakdown, rsInput, tbColumn, dbTableName, epp, limit1=0, limit2=0, extra = "", extra1 = "",start_hour = "00:00", end_hour = "00:00", max_retries = 5):
    dateCaller = dateGenerator(startDate, endDate, period)
    defaultColumn = ["site_code", "dimension", "breakdown", "period", "start_date", "end_date", "is_epp"]
    
    if extra != "":
        defaultColumn.append("extra")
    if extra1 != "":
        defaultColumn.append("extra1")

    newColumn = defaultColumn + tbColumn

    startDate = dateCaller[0]
    endDate = dateCaller[1]

    rsList = returnRsList(epp, rsInput)

    for j in range(len(rsList)):
        for i in range(len(startDate)):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    start = time.time()
                    secondCaller(startDate[i], endDate[i], jsonFile, jsonFilebreakdown, rsList[j],  period, newColumn, dbTableName, epp, limit1, limit2, extra, extra1, start_hour, end_hour)
                    break

                except EmptyDataError : 
                    print(rsList[j],startDate[i], endDate[i] )
                    break

                except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                    retry_count += 1
                    continue


                if retry_count == max_retries:
                    print(f"Max retries {max_retries} reached. Moving to the next task.")
                else:
                    continue   

            timeSec = round(time.time() - start, 2)
            print("Time took: ", timeSec, "sec")

def retrieve_RB(start_date, end_date, jsonLocation, rsInput, tbColumn, dbTableName, epp, limit=0, Biz_type = "", Device_type = "", Division = "", Category = "", max_retries = 5):
    start_hour="00:00"
    end_hour="00:00"
    period = "daily"
    dateCaller = dateGenerator(start_date, end_date, period)
    site_code_rs = False
    tbColumn = tbColumnGeneratorRB(tbColumn, False, False, True, site_code_rs)
    
    startDate = dateCaller[0]
    endDate = dateCaller[1]

    rsList = returnRsList(epp, rsInput)

    for j in range(len(rsList)):
        for i in range(len(startDate)):
            retry_count = 0
            while retry_count < max_retries:
                try:
                  start = time.time()
                  refineRsIDChangeRB(startDate[i], endDate[i], jsonLocation, rsList[j], period, tbColumn, dbTableName, epp, limit, Biz_type,Device_type,Division,Category,"",start_hour, end_hour)
                  break  
                except EmptyDataError : 
                    print(rsList[j],startDate[i], endDate[i] )
                    break
                except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                    retry_count += 1
                    continue


                if retry_count == max_retries:
                    print(f"Max retries {max_retries} reached. Moving to the next task.")
            else:
                continue  
            timeSec = round(time.time() - start, 2)
            print("Time took: ", timeSec, "sec")

       
def retrieve_RB_AE(start_date, end_date, jsonLocation, rsInput, tbColumn, dbTableName, epp, limit=0, Biz_type = "", Device_type = "", Division = "", Category = "", site_code_ae ="", max_retries = 5):
    start_hour="00:00"
    end_hour="00:00"
    period = "daily"
    dateCaller = dateGenerator(start_date, end_date, period)
    site_code_rs = False
    tbColumn = tbColumnGeneratorRB(tbColumn, False, False, True, site_code_rs)
    
    startDate = dateCaller[0]
    endDate = dateCaller[1]

    rsList = returnRsList(epp, rsInput)

    for j in range(len(rsList)):
        for i in range(len(startDate)):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    start = time.time()
                    refineRsIDChangeRB(startDate[i], endDate[i], jsonLocation, rsList[j], period, tbColumn, dbTableName, epp, limit, Biz_type,Device_type,Division,Category,site_code_ae,start_hour, end_hour)
                    break  
                except EmptyDataError : 
                    print(rsList[j],startDate[i], endDate[i] )
                    break
                except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                    retry_count += 1
                    continue


                if retry_count == max_retries:
                    print(f"Max retries {max_retries} reached. Moving to the next task.")
            else:
                continue  
            timeSec = round(time.time() - start, 2)
            print("Time took: ", timeSec, "sec")   

def retrieve_by_RS_breakdownTotal(startDate, endDate, period, jsonFile, jsonFilebreakdown, rsInput, tbColumn, dbTableName, epp, limit1=0, limit2=0, extra = "", extra1 = "", start_hour = "00:00", end_hour = "00:00", max_retries = 5):
    dateCaller = dateGenerator(startDate, endDate, period)
    defaultColumn = ["site_code", "dimension", "breakdown", "period", "start_date", "end_date", "is_epp"]
    
    if extra != "":
        defaultColumn.append("extra")
    if extra1 != "":
        defaultColumn.append("extra1")

    newColumn = defaultColumn + tbColumn

    startDate = dateCaller[0]
    endDate = dateCaller[1]

    rsList = returnRsList(epp, rsInput)

    for j in range(len(rsList)):
        for i in range(len(startDate)):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    start = time.time()
                    refineRsIDChangeTotal(startDate[i], endDate[i], jsonFile, rsList[j], period, newColumn, dbTableName, epp, limit1, extra, extra1, start_hour, end_hour)
                    secondCaller(startDate[i], endDate[i], jsonFile, jsonFilebreakdown, rsList[j],  period, newColumn, dbTableName, epp, limit1, limit2, extra, extra1, start_hour, end_hour)
                    break
                except EmptyDataError : 
                    print(rsList[j],startDate[i], endDate[i] )
                    break
                except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                   retry_count += 1
                   continue
                if retry_count == max_retries:
                    print(f"Max retries {max_retries} reached. Moving to the next task.")
            else:
                continue   

            timeSec = round(time.time() - start, 2)
            print("Time took: ", timeSec, "sec")


def retrieve_SecondLevelTotal(start_date, end_date, period, jsonLocation, jsonLocation_breakdown,tbColumn, dbTableName, epp, limit1=0, limit2=0, extra = "", extra1 = "", start_hour="00:00", end_hour="00:00", site_code="", max_retries = 5):
    dateCaller = dateGenerator(start_date, end_date, period)
    if_site_code = checkSiteCode(readJson(jsonLocation)["dimension"])

    if returnRsID(jsonLocation) == "sssamsungnewus":
        if_site_code = True

    site_code_rs = False
    tbColumn = tbColumnGenerator(tbColumn, if_site_code, True, False, site_code_rs)
    
    startDate = dateCaller[0]
    endDate = dateCaller[1]

    for i in range(len(startDate)):
        retry_count = 0
        while retry_count < max_retries:
            try:
                start = time.time()
                refinedFrameTotal(startDate[i], endDate[i], period, jsonLocation, tbColumn, dbTableName, epp, if_site_code, site_code_rs, limit1, extra, extra1, start_hour, end_hour, site_code)
                StackbreakValue(startDate[i], endDate[i], period, jsonLocation, jsonLocation_breakdown, tbColumn, dbTableName, epp, limit1, limit2, extra, extra1, start_hour, end_hour, site_code)
                break
            except EmptyDataError : 
                print(rsList[j],startDate[i], endDate[i] )
                break
            except (KeyError, IndexError, AttributeError, ConnectionError, ConnectionResetError, RetryableServerError):
                retry_count += 1
                continue

            if retry_count == max_retries:
                print(f"Max retries {max_retries} reached. Moving to the next task.")
        else:
            continue  

        timeSec = round(time.time() - start, 2)
        print("Time took: ", timeSec, "sec")

################UPDATE
def retrieve_RB_parallel(start_date, end_date, jsonLocation, rsInput, tbColumn, dbTableName, epp, limit=0, Biz_type="", Device_type="", Division="", Category="", max_retries=5, max_workers=5):
    period = "daily"
    start_hour = "00:00"
    end_hour = "00:00"
    dateCaller = dateGenerator(start_date, end_date, period)
    startDates = dateCaller[0]
    endDates = dateCaller[1]
    site_code_ae =""

    site_code_rs = False
    tbColumn = tbColumnGeneratorRB(tbColumn, False, False, True, site_code_rs)

    rsList = returnRsList(epp, rsInput)

    # task 리스트 생성
    tasks = []
    for rs in rsList:
        for sd, ed in zip(startDates, endDates):
            tasks.append((
                sd, ed, jsonLocation, rs, period, tbColumn, dbTableName, epp, limit, Biz_type, Device_type, Division, Category , site_code_ae, start_hour, end_hour, max_retries
            ))

    print(f"총 작업 수 : {len(tasks)}개")

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
       futures = [executor.submit(worker_refine_RB, t) for t in tasks]
       for f in as_completed(futures):
           try:
               f.result()
           except Exception as e:
               print("Unhandled error:", e)

def retrieve_RB_AE_parallel(start_date, end_date, jsonLocation, rsInput, tbColumn, dbTableName, epp, limit=0, Biz_type="", Device_type="", Division="", Category="", site_code_ae ="", max_retries=5, max_workers=5):
    period = "daily"
    start_hour = "00:00"
    end_hour = "00:00"
    dateCaller = dateGenerator(start_date, end_date, period)
    startDates = dateCaller[0]
    endDates = dateCaller[1]

    site_code_rs = False
    tbColumn = tbColumnGeneratorRB(tbColumn, False, False, True, site_code_rs)

    rsList = returnRsList(epp, rsInput)

    # task 리스트 생성
    tasks = []
    for rs in rsList:
        for sd, ed in zip(startDates, endDates):
            tasks.append((
                sd, ed, jsonLocation, rs, period, tbColumn, dbTableName, epp, limit, Biz_type, Device_type, Division, Category , site_code_ae, start_hour, end_hour, max_retries
            ))

    print(f"총 작업 수 : {len(tasks)}개")

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
       futures = [executor.submit(worker_refine_RB, t) for t in tasks]
       for f in as_completed(futures):
           try:
               f.result()
           except Exception as e:
               print("Unhandled error:", e)

def retrieve_by_RS_parallel(start_date, end_date, period, jsonLocation, rsInput, tbColumn, dbTableName, epp, limit=0, extra="", extra1="", start_hour="00:00", end_hour="00:00", max_retries=5, max_workers=5):

    dateCaller = dateGenerator(start_date, end_date, period)
    site_code_rs = False
    tbColumn = tbColumnGenerator(tbColumn, False, False, True, site_code_rs)

    startDates = dateCaller[0]
    endDates = dateCaller[1]

    rsList = returnRsList(epp, rsInput)

    # task 리스트 생성
    tasks = []
    for rs in rsList:
        for sd, ed in zip(startDates, endDates):
            tasks.append(( 
		sd, ed, jsonLocation, rs, period, tbColumn, dbTableName, epp, limit, extra, extra1, start_hour, end_hour, max_retries
            ))

    print(f"총 작업 수 : {len(tasks)}개")

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_refine_RS, t) for t in tasks]

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print("Unhandled error:", e)

