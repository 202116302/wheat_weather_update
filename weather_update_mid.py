import datetime
import time
import pandas as pd
import requests
import json
from urllib.parse import urlparse, parse_qs
import csv

today = datetime.datetime.today().strftime("%Y%m%d")  # 오늘날짜
y = datetime.date.today() - datetime.timedelta(days=1)
f = datetime.date.today() + datetime.timedelta(days=3)
yesterday = y.strftime("%Y%m%d")  # 어제날짜
future = f.strftime("%Y%m%d")

now = datetime.datetime.now()  # 현재 날짜, 시각
hour = now.hour  # 현재시각

# ----요청 시각, 날짜 재조정
if hour < 6:
    today = yesterday

# 중기육상예보(강수 확률, 날씨 예보)
url = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
# 중기기온조희(예상최저, 최고 기온)
url2 = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'

# 중기육상예보
# 전라북도 : 11F10000

params_url = {'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
              'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
              'regId': '11F10000', 'tmFc': f'{today}0600'}

# regIdd , 중기기온조회
# 남원 : 11F10401
# 익산 : 11F10202

params_url2 = {'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
               'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
               'regId': '11F10401', 'tmFc': f'{today}0600'}

response_land = requests.get(url, params=params_url)
response_midta = requests.get(url2, params=params_url2)

item_land = response_land.content.decode('utf-8')
item_midta = response_midta.content.decode('utf-8')


df_land = json.loads(item_land)
df_midta = json.loads(item_midta)
midta_value = df_midta['response']['body']['items']['item']
land_value = df_land['response']['body']['items']['item']

weather_mid = {}
for i in range(3, 8):
    f = datetime.date.today() + datetime.timedelta(days=i)
    f = f.strftime("%Y%m%d")
    a = {f'rf_{i}_am': f"{land_value[0][f'rnSt{i}Am']}", f'rf_{i}_pm': f"{land_value[0][f'rnSt{i}Pm']}",
         f'wf_{i}_am': f"{land_value[0][f'wf{i}Am']}", f'wf_{i}_pm': f"{land_value[0][f'wf{i}Pm']}",
         f'tamin_{i}': f"{midta_value[0][f'taMin{i}']}", f'tamax_{i}': f"{midta_value[0][f'taMax{i}']}"}
    weather_mid[f] = a

nam_weather_mid = json.dumps(weather_mid, ensure_ascii=False)
print(nam_weather_mid)


df = pd.read_csv('weather_month.csv', encoding='euc-kr')

df2 = df[['평균기온(℃)', '평균최고기온(℃)', '평균최저기온(℃)']]
df2 = df2.rename(columns={'평균기온(℃)': 'tavg', '평균최고기온(℃)': 'tmax', '평균최저기온(℃)': 'tmin'})
# df2.to_csv('weather_month_data.csv', encoding='utf-8-sig', index=False)


# -------------------------------------------- 과거 기상 데이터 조회 -----------------
url3 = "https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionAjax.do"
header = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "XTVID=A230711135728760398; _harry_lang=ko-KR; _harry_fid=hh1197145764; JSESSIONID=CC6ZWZPxhJPbAT4jcugELpg4ucAF38JzKRgpO018w0ii1B7vxoTu1GBB7RUZWCsD.was01_servlet_engine5; _harry_ref=; _harry_url=https^%^3A//data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do^%^3FpgmNo^%^3D179^%^26menuNo^%^3D440^%^26pageIndex^%^3D^%^26minTa^%^3D25.0^%^26stnGroupSns^%^3D^%^26selectType^%^3D1^%^26mddlClssCd^%^3DSFC01^%^26lastDayOfMonth^%^3D31^%^26startDt^%^3D20100101^%^26endDt^%^3D20230724^%^26schType^%^3D1^%^26txtStnNm^%^3D^%^26stnId^%^3D^%^26areaId^%^3D^%^26ureaType^%^3D1^%^26dataFormCd^%^3D2^%^26startYear^%^3D2013^%^26endYear^%^3D2023^%^26tempInputVal^%^3D1^%^26precInputVal^%^3D1^%^26windInputVal^%^3D1^%^26rhmInputVal^%^3D1^%^26icsrInputVal^%^3D1^%^26symbol^%^3D1^%^26inputInt^%^3D^%^26condit^%^3D^%^26symbol2^%^3D1^%^26inputInt2^%^3D^%^26monthCheck^%^3DY^%^26startMonth^%^3D01^%^26endMonth^%^3D12^%^26startDay^%^3D01^%^26endDay^%^3D31^%^26sesn^%^3D1; _harry_hsid=A230725023423777408; _harry_dsid=A230725023423778927; xloc=340X1080",
    "Origin": "https ://data.kma.go.kr",
    "Pragma": "no-cache",
    "Referer": "https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do?curl^%^20^%^22https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionAjax.do^%^22^%^20^^^%^20-H^%^20^%^22Accept:^%^20application/json,^%^20text/javascript,^%^20*/*;^%^20q=0.01^%^22^%^20^^^%^20-H^%^20^%^22Accept-Language:^%^20ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7^%^22^%^20^^^%^20-H^%^20^%^22Cache-Control:^%^20no-cache^%^22^%^20^^^%^20-H^%^20^%^22Connection:^%^20keep-alive^%^22^%^20^^^%^20-H^%^20^%^22Content-Type:^%^20application/x-www-form-urlencoded;^%^20charset=UTF-8^%^22^%^20^^^%^20-H^%^20^%^22Cookie:^%^20XTVID=A230711135728760398;^%^20_harry_lang=ko-KR;^%^20_harry_fid=hh1197145764;^%^20JSESSIONID=CC6ZWZPxhJPbAT4jcugELpg4ucAF38JzKRgpO018w0ii1B7vxoTu1GBB7RUZWCsD.was01_servlet_engine5;^%^20_harry_ref=;^%^20_harry_url=https^^^%^^3A//data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do^^^%^^3FpgmNo^^^%^^3D179^^^%^^26menuNo^^^%^^3D440^^^%^^26pageIndex^^^%^^3D^^^%^^26minTa^^^%^^3D25.0^^^%^^26stnGroupSns^^^%^^3D^^^%^^26selectType^^^%^^3D1^^^%^^26mddlClssCd^^^%^^3DSFC01^^^%^^26lastDayOfMonth^^^%^^3D31^^^%^^26startDt^^^%^^3D20100101^^^%^^26endDt^^^%^^3D20230724^^^%^^26schType^^^%^^3D1^^^%^^26txtStnNm^^^%^^3D^^^%^^26stnId^^^%^^3D^^^%^^26areaId^^^%^^3D^^^%^^26ureaType^^^%^^3D1^^^%^^26dataFormCd^^^%^^3D2^^^%^^26startYear^^^%^^3D2013^^^%^^26endYear^^^%^^3D2023^^^%^^26tempInputVal^^^%^^3D1^^^%^^26precInputVal^^^%^^3D1^^^%^^26windInputVal^^^%^^3D1^^^%^^26rhmInputVal^^^%^^3D1^^^%^^26icsrInputVal^^^%^^3D1^^^%^^26symbol^^^%^^3D1^^^%^^26inputInt^^^%^^3D^^^%^^26condit^^^%^^3D^^^%^^26symbol2^^^%^^3D1^^^%^^26inputInt2^^^%^^3D^^^%^^26monthCheck^^^%^^3DY^^^%^^26startMonth^^^%^^3D01^^^%^^26endMonth^^^%^^3D12^^^%^^26startDay^^^%^^3D01^^^%^^26endDay^^^%^^3D31^^^%^^26sesn^^^%^^3D1;^%^20_harry_hsid=A230725023423777408;^%^20_harry_dsid=A230725023423778927;^%^20xloc=340X1080^%^22^%^20^^^%^20-H^%^20^%^22Origin:^%^20https://data.kma.go.kr^%^22^%^20^^^%^20-H^%^20^%^22Pragma:^%^20no-cache^%^22^%^20^^^%^20-H^%^20^%^22Referer:^%^20https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do?pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20100101&endDt=20230724&schType=1&txtStnNm=&stnId=&areaId=&ureaType=1&dataFormCd=2&startYear=2013&endYear=2023&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=12&startDay=01&endDay=31&sesn=1^%^22^%^20^^^%^20-H^%^20^%^22Sec-Fetch-Dest:^%^20empty^%^22^%^20^^^%^20-H^%^20^%^22Sec-Fetch-Mode:^%^20cors^%^22^%^20^^^%^20-H^%^20^%^22Sec-Fetch-Site:^%^20same-origin^%^22^%^20^^^%^20-H^%^20^%^22User-Agent:^%^20Mozilla/5.0^%^20(Linux;^%^20Android^%^206.0;^%^20Nexus^%^205^%^20Build/MRA58N)^%^20AppleWebKit/537.36^%^20(KHTML,^%^20like^%^20Gecko)^%^20Chrome/114.0.0.0^%^20Mobile^%^20Safari/537.36^%^22^%^20^^^%^20-H^%^20^%^22X-Requested-With:^%^20XMLHttpRequest^%^22^%^20^^^%^20-H^%^20^%^22sec-ch-ua:^%^20^^^\^\^^^%^22Not.A/Brand^^^\^\^^^%^22;v=^^^\^\^^^%^228^^^\^\^^^%^22,^%^20^^^\^\^^^%^22Chromium^^^\^\^^^%^22;v=^^^\^\^^^%^22114^^^\^\^^^%^22,^%^20^^^\^\^^^%^22Google^%^20Chrome^^^\^\^^^%^22;v=^^^\^\^^^%^22114^^^\^\^^^%^22^%^22^%^20^^^%^20-H^%^20^%^22sec-ch-ua-mobile:^%^20?1^%^22^%^20^^^%^20-H^%^20^%^22sec-ch-ua-platform:^%^20^^^\^\^^^%^22Android^^^\^\^^^%^22^%^22^%^20^^^%^20--data-raw^%^20^%^22fileType=&pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20100101&endDt=20230724&schType=1&txtStnNm=^^^%^^EB^^^%^^82^^^%^^A8^^^%^^EC^^^%^^9B^^^%^^90&stnId=247&areaId=&ureaType=1&dataFormCd=2&startYear=2013&endYear=2023&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=12&startDay=01&endDay=31&sesn=1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": 'Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": "Android",
}

# 파라미터 구하기
# uri = "https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionAjax.do?fileType=&pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20100101&endDt=20230724&schType=1&txtStnNm=^%^EB^%^82^%^A8^%^EC^%^9B^%^90&stnId=247&areaId=&ureaType=1&dataFormCd=2&startYear=2013&endYear=2023&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=12&startDay=01&endDay=31&sesn=1"
# parse_result = urlparse(uri)
# params = parse_qs(parse_result.query)
# print(params)

# param = {'pgmNo': '179', 'menuNo': '440', 'minTa': '25.0', 'selectType': '1', 'mddlClssCd': 'SFC01', 'lastDayOfMonth': '31',
#          'startDt': '20100101', 'endDt': '20230723', 'schType': '1', 'txtStnNm': '^%^EB^%^82^%^A8^%^EC^%^9B^%^90', 'stnId': '247', 'ureaType': '1', 'dataFormCd': '2',
#          'startYear': '2013', 'endYear': '2023', 'tempInputVal': '1', 'precInputVal': '1', 'windInputVal': '1', 'rhmInputVal': '1', 'icsrInputVal': '1', 'symbol': '1',
#          'symbol2': '1', 'monthCheck': 'Y', 'startMonth': '01', 'endMonth': '12', 'startDay': '01', 'endDay': '31', 'sesn': '1'}

data = "fileType=&pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20000101&endDt=20230724&schType=1&txtStnNm=%EB%82%A8%EC%9B%90&stnId=247&areaId=&ureaType=1&dataFormCd=2&startYear=2003&endYear=2022&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=12&startDay=01&endDay=31&sesn=1"
response = requests.post(url3, headers=header, data=data)
result = response.text
data = json.loads(result)
content = data['data']
content_tavg = [x['avgTa'] for x in content]
content_tmax = [x['avgDmaxTa'] for x in content]
content_tmin = [x['avgDminTa'] for x in content]
date = [x['tma'] for x in content]

namwon_20 = {'tavg': content_tavg, 'tmax': content_tmax, 'tmin': content_tmin, 'date': date}



#----------------------------------------------------현재 기상 데이터 ----------------------------------------



url4 = "https://www.weather.go.kr/w//renew2021/rest/main/current-weather-obs.do"

response_now = requests.get(url4)
result_now = response_now.text
data_now = json.loads(result_now)
content_now = data_now['data']
namwon_now = [x for x in content_now if x['stnKo'] == '남원']

nam_json = json.dumps(namwon_now[0], ensure_ascii=False)


























