# Created by Sunkyeong Lee
# Inquiry : sunkyeong.lee@concentrix.com / sunkyong9768@gmail.com
# Updated & Managed by Youngkwang Cho
# Inquiry : youngkwang.Cho@concentrix.com / ykc124@naver.com
# 251223 RS INPUT 변수에 EU-VRS 6개국 추가및 UK_OLD 명칭 변경

from datetime import datetime, timedelta
from calendar import monthrange


def dateConverter(date):
    return datetime.strptime(str(date), '%Y-%m-%d').date()


def lastDayofMonth(date_value):
    return date_value.replace(day = monthrange(date_value.year, date_value.month)[1])


def dateGenerator(startDate, endDate, period):
    start_date = dateConverter(startDate)
    end_date = dateConverter(endDate)

    how_long = (end_date - start_date).days

    if (period == "daily" or period == "Daily"):
        date_list = []
        date_list.append(str(start_date))
        for i in range(how_long):
            start_date += timedelta(days=1)
            start_date_v2 = str(start_date)
            date_list.append(start_date_v2)
        
        return date_list, date_list

    elif (period == "weekly" or period == "Weekly"):
        dateKeep = start_date
        dateKeep_end = dateKeep + timedelta(days=6)

        startDate = []
        endDate = []
        startDate.append(str(dateKeep))
        endDate.append(str(dateKeep_end))

        while dateKeep < end_date:
            dateKeep += timedelta(days=7)
            dateKeep_end += timedelta(days=7)

            startDate.append(str(dateKeep))
            endDate.append(str(dateKeep_end))

        startDate.pop()
        endDate.pop()

        return startDate, endDate

# 230525 revised by Hyunsung Park (Monthly)
    elif (period == "monthly" or period == "Monthly"):
        startDate = []
        endDate = []

        startDate.append(str(start_date))

        startDate_keep = start_date
        endDate_keep = end_date

        while startDate_keep <= lastDayofMonth(end_date):
            if startDate_keep.year == end_date.year and startDate_keep.month == end_date.month:
                # 230601 end date is autofixed to the end of the month
                endDate.append(str(lastDayofMonth(end_date)))
                startDate_keep = endDate_keep + timedelta(days=1)
                startDate.append(str(startDate_keep))
                break

            else:
                endDate_keep = lastDayofMonth(startDate_keep)
                startDate_keep = endDate_keep + timedelta(days=1)
                startDate.append(str(startDate_keep))
                endDate.append(str(endDate_keep))

            startDate_keep = lastDayofMonth(startDate_keep)
        startDate.pop()
        return startDate, endDate

    elif (period == "all" or period == "All"):
        startDate = []
        endDate = []

        startDate.append(str(start_date))
        endDate.append(str(end_date))

        return startDate, endDate
    
    else:
        raise Exception("Type within the followings; daily, weekly, monthly, all")

def rsListGenerator(inputSiteCode, targetRSList):
    finalList = []
    for i in range(len(inputSiteCode)):
        for j in range(len(targetRSList)):
            if inputSiteCode[i] in targetRSList[j]:
                finalList.append(targetRSList[j])

    return finalList


def returnRsList(epp, inputSiteCode):
    #22.02.10 kz_kz, ua epp 추가
    #22.02.16 mst_vs 추가
    #22.04.01 si, hr epp 추가
    #22.07.26 iq_ar, lb 추가
    #22.09.01 cl epp 추가
    #22.10.24 ph epp 추가
    #23.02.02 iq_ar epp 추가
    #23.03.03 jp epp 추가
    #23.04.24 mn, ge 추가
    #24.04.16 semiconductor 추가
    #24.06.05 uk 수정 (UK VRS > UK, UK RS > UK_EPP)
    #24.08.13 MST 추가
    #24.08.26 ku추가
    defaultEpp = [["us", "sssamsungnewus"], ["ae", "sssamsung4aeepp"], ["at", "sssamsung4atepp"], ["au", "sssamsung4auepp"], ["be", "sssamsung4beepp"], ["ca", "sssamsung4caepp"], ["ch", "sssamsung4chepp"], ["cn", "sssamsung4cnepp"], ["cz", "sssamsung4czepp"], ["de", "sssamsung4deepp"], ["dk", "sssamsung4dkepp"], ["ee", "sssamsung4eeepp"], ["eg", "sssamsung4egepp"], ["es", "sssamsung4esepp"], ["fi", "sssamsung4fiepp"], ["fr", "sssamsung4frepp"], ["hk", "sssamsung4hkepp"], ["hu", "sssamsung4huepp"], ["id", "sssamsung4idepp"], ["il", "sssamsung4ilepp"], ["in", "sssamsung4inepp"], ["it", "sssamsung4itepp"], ["levant", "sssamsung4levantepp"], ["lt", "sssamsung4ltepp"], ["lv", "sssamsung4lvepp"], ["my", "sssamsung4myepp"], ["n_africa", "sssamsung4nafricaepp"], ["nl", "sssamsung4nlepp"], ["no", "sssamsung4noepp"], ["nz", "sssamsung4nzepp"], ["pk", "sssamsung4pkepp"], ["pt", "sssamsung4ptepp"], ["ru", "sssamsung4ruepp"], ["sa", "sssamsung4saepp"], ["se", "sssamsung4seepp"], ["sec", "sssamsung4secepp"], ["sg", "sssamsung4sgepp"], ["sk", "sssamsung4skepp"], ["th", "sssamsung4thepp"], ["tw", "sssamsung4twepp"], ["uk", "sssamsung4ukepp"], ["uk_epp", "sssamsung4ukepp"], ["vn", "sssamsung4vnepp"], ["za", "sssamsung4zaepp"], ["kz_kz", "sssamsung4kzkzepp"], ["ua", "sssamsung4uaepp"], ["si", "sssssamsung4siepp"], ["hr", "sssamsung4hrepp"], ["cl", "sssamsung4clepp"], ["ph", "sssamsung4phepp"], ["africa_en", "sssamsung4africaenepp"], ["co", "sssamsung4coepp"], ["gr", "sssamsung4grepp"], ["ie", "sssamsung4ieepp"], ["mx", "sssamsung4mxepp"], ["pe", "sssamsung4peepp"], ["pl", "sssamsung4plepp"], ["ro", "sssamsung4roepp"], ["iq_ar", "sssamsung4iqarepp"], ["jp", "sssamsung4jpepp"]]
    defaultNone = [["us", "sssamsungnewus"], ["sec", "sssamsung4sec"], ["ae", "sssamsung4ae"], ["ae_ar", "sssamsung4aear"], ["africa_en", "sssamsung4africaen"], ["africa_fr", "sssamsung4africafr"], ["africa_pt", "sssamsung4africapt"], ["al", "sssamsung4al"], ["ar", "sssamsung4ar"], ["at", "sssamsung4at"], ["au", "sssamsung4au"], ["ba", "sssamsung4ba"], ["be", "vrs_samsun0_p6webmstbelgiumestor"], ["be_old", "sssamsung4be"], ["be_fr", "sssamsung4befr"], ["bg", "sssamsung4bg"], ["br", "sssamsung4br"], ["ca", "sssamsung4ca"], ["ca_fr", "sssamsung4cafr"], ["ch", "sssamsung4ch"], ["ch_fr", "sssamsung4chfr"], ["cl", "sssamsung4cl"], ["cn", "sssamsung4cn"], ["co", "sssamsung4co"], ["cz", "sssamsung4cz"], ["de", "vrs_samsun0_p6webmstgermanyestor_0"], ["de_old", "sssamsung4de"], ["dk", "sssamsung4dk"], ["ee", "sssamsung4ee"], ["eg", "sssamsung4eg"], ["es", "vrs_samsun0_p6webmstspainestoreb"], ["es_old", "sssamsung4es"], ["fi", "sssamsung4fi"], ["fr", "sssamsung4fr"], ["gr", "sssamsung4gr"], ["hk", "sssamsung4hk"], ["hk_en", "sssamsung4hken"], ["hr", "sssamsung4hr"], ["hu", "sssamsung4hu"], ["id", "sssamsung4id"], ["ie", "sssamsung4ie"], ["il", "sssamsung4il"], ["in", "sssamsung4in"], ["iran", "sssamsung4iran"], ["it", "sssamsung4it"], ["jp", "sssamsung4jp"], ["kz_kz", "sssamsung4kzkz"], ["kz_ru", "sssamsung4kzru"], ["latin", "sssamsung4latin"], ["latin_en", "sssamsung4latinen"], ["levant", "sssamsung4levant"], ["levant_ar", "sssamsung4levantar"], ["lt", "sssamsung4lt"], ["lv", "sssamsung4lv"], ["mk", "sssamsung4mk"], ["mm", "sssamsung4mm"], ["mx", "sssamsung4mx"], ["my", "sssamsung4my"], ["n_africa", "sssamsung4nafrica"], ["nl", "vrs_samsun0_p6webmstnetherlandse_0"], ["nl_old", "sssamsung4nl"], ["no", "sssamsung4no"], ["nz", "sssamsung4nz"], ["pe", "sssamsung4pe"], ["ph", "sssamsung4ph"], ["pk", "sssamsung4pk"], ["pl", "sssamsung4pl"], ["ps", "sssamsung4ps"], ["pt", "vrs_samsun0_p6webmstportugalesto"], ["pt_old", "sssamsung4pt"], ["py", "sssamsung4py"], ["ro", "sssamsung4ro"], ["rs", "sssamsung4rs"], ["ru", "sssamsung4ru"], ["sa", "sssamsung4sa"], ["sa_en", "sssamsung4saen"], ["se", "sssamsung4se"], ["sg", "sssamsung4sg"], ["si", "sssamsung4si"], ["sk", "sssamsung4sk"], ["th", "sssamsung4th"], ["tr", "sssamsung4tr"], ["tw", "sssamsung4tw"], ["ua", "sssamsung4ua"], ["uk", "vrs_samsun0_p6webmstukcopy"], ["uk_old", "sssamsung4uk"], ["uy", "sssamsung4uy"], ["uz_ru", "sssamsung4uzru"], ["uz_uz", "sssamsung4uzuz"], ["vn", "sssamsung4vn"], ["za", "sssamsung4za"], ["az", "sssamsung4az"], ["bd", "sssamsung4bd"],["ku", "sssamsung4ku"], ["mst_sena", "vrs_samsun0_p4webmstsena_0"], ["mst_sehk", "vrs_samsun0_p6webmstsehk"], ["mst_sebn", "vrs_samsun0_p4websebn"], ["mst_mena", "vrs_samsun0_p4webmstmena"], ["mst_seca", "vrs_samsun0_p4webmstseca"], ["mst_eu", "vrs_samsun0_p4webmsteu_0"], ["mst_seao", "vrs_samsun0_p4webmstseao"], ["iq_ar", "sssamsung4iqar"], ["lb", "sssamsung4lb"], ["mn", "sssamsung4mn"], ["ge", "sssamsung4ge"],["ds-global","sssamsung4b2bsemi"], ["ds-cn","sssamsung4b2bsemicn"],["ds-us","sssamsung4b2bsemius"],["ds-kr","sssamsung4b2bsemikr"],["ds-emea","sssamsung4b2bsemiemea"],["ds-jp","sssamsung4b2csemi"],["ds-total","sssamsung4b2bsemiconductor"],["mst","sssamsung4mstglobal"]]

    if epp == True:
        return rsListGenerator(inputSiteCode, defaultEpp)
    else:
        return rsListGenerator(inputSiteCode, defaultNone)


def tbColumnGenerator(tbColumn, if_site_code, breakdown, epp, site_code_rs):
    if site_code_rs == True:
        breakdown = False
        if_site_code = True

    defaultColumn = ["site_code", "period", "start_date", "end_date", "is_epp"]
    if epp == True:
        defaultColumn.insert(1, "breakdown")
        defaultColumn.insert(6, "is_epp_integ")
    else:
        if breakdown == False:
            if if_site_code == True:
                defaultColumn = defaultColumn
            else:
                defaultColumn.insert(1, "dimension")
        
        else:
            if if_site_code == True:
                defaultColumn.insert(1, "breakdown")
            else:
                defaultColumn[0] = "dimension"
                defaultColumn.insert(1, "breakdown")
    
    for i in range(len(tbColumn)):
        defaultColumn.append(tbColumn[i])
    
    return defaultColumn


def tbColumnGeneratorRB(tbColumn, if_site_code, breakdown, epp, site_code_rs):  ##tbColumn, False, False, True, site_code_rs
    if site_code_rs == True:
        breakdown = False
        if_site_code = True
    defaultColumn = ["site_code", "RS ID","Biz_type","Division","Category","Device_type","Date","Channel_Raw"]

  #  defaultColumn = ["site_code", "period", "date", "end_date", "is_epp"]    
    for i in range(len(tbColumn)):
        defaultColumn.append(tbColumn[i])
    
    return defaultColumn