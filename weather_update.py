import json
from collections import Counter
import statistics
import requests
from json import dumps
from tinydb import TinyDB, Query, where
import datetime
import pandas as pd
import redis
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# 플라스크 선언
# app = Flask(__name__)
# app.config['JSON_AS_ASCII'] = False
#


try:
    from urllib import urlencode, unquote
    from urlparse import urlparse, parse_qsl, ParseResult
except ImportError:
    # Python 3 fallback
    from urllib.parse import (
        urlencode, unquote, urlparse, parse_qsl, ParseResult
    )

url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'

# 인증키
serviceKey = "HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ=="
# 페이지번호
pageNo = "1"
# 한 페이지 결과 수 (행 수)
numOfRaws = "1000"
# 자료 형식 json or xml
datatype = "JSON"

# 예보지점의 x, y 좌표값
nx_namwon = '68'
ny_namwon = '80'

nx_iksan = '59'
ny_iksan = '94'

# 평창군 대화면
nx_pyeongchang = '85'
ny_pyeongchang = '126'

# 부안군 백산면
nx_buan = '57'
ny_buan = '86'


# 요일 나타내는 함수
def what_day_is_it(date):
    days = ['월', '화', '수', '목', '금', '토', '일']
    day = date.weekday()

    return days[day]

# 지역별 파라미터 + url 함수
def add_url_params(url, params):
    url = unquote(url)
    parsed_url = urlparse(url)  # urlparse == url을 인코딩해줌
    get_args = parsed_url.query
    parsed_get_args = dict(parse_qsl(get_args))
    parsed_get_args.update(params)

    parsed_get_args.update(
        {k: dumps(v) for k, v in parsed_get_args.items()
         if isinstance(v, (bool, dict))}
    )

    encoded_get_args = urlencode(parsed_get_args, doseq=True)
    new_url = ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()
    res = requests.get(new_url)

    items = res.json().get('response').get('body').get('items').get('item')
    return items


# 날씨 정보 추출 함수
def sky(loc):
    items = add_url_params(url, loc)
    weather_total = dict()
    rainfall = dict()
    humid = dict()
    sky = dict()
    tmin = dict()
    tmax = dict()
    weather_date = []
    days = []
    pop_0 = []
    pop_1 = []
    pop_2 = []
    pop_3 = []
    pop_4 = []
    time = []
    pop = [pop_0, pop_1, pop_2, pop_3, pop_4]

    # 날짜 뽑기
    for x in items:
        if not x['fcstDate'] in weather_date:
            weather_date.append(x["fcstDate"])

    # 강수확률(%)
    for i in range(len(weather_date)):
        for x in items:
            if x['fcstDate'] == weather_date[i] and x["category"] == "POP":
                pop[i].append(int(x['fcstValue']))

    for i in range(len(weather_date)):
        pop_mean = statistics.mean(pop[i])
        weather_total[f'{weather_date[i]}_rainfall'] = f"{pop_mean:.1f}"
        rainfall[f'{weather_date[i]}'] = f"{pop_mean:.1f}%"
        pop[i].clear()

    # 습도(%)
    for i in range(len(weather_date)):
        for x in items:
            if x['fcstDate'] == weather_date[i] and x["category"] == "REH":
                pop[i].append(int(x['fcstValue']))

    for i in range(len(weather_date)):
        reh_mean = statistics.mean(pop[i])
        weather_total[f'{weather_date[i]}_humid'] = f"{reh_mean:.1f}"
        humid[f'{weather_date[i]}'] = f"{reh_mean:.1f}%"
        pop[i].clear()

    # 하늘 상태 0 ~ 1 맑음 , 2 ~ 5 구름 많음 , 6 ~ 10 흐림
    for i in range(len(weather_date)):
        for x in items:
            if x['fcstDate'] == weather_date[i] and x["category"] == "SKY":
                pop[i].append(x['fcstValue'])

    for i in range(len(weather_date)):
        count_sky = Counter(pop[i])
        sky_max = count_sky.most_common(1)
        max_sky = list(sky_max[0])[0]
        weather_total[f'{weather_date[i]}_sky'] = max_sky
        sky[f'{weather_date[i]}'] = max_sky
        # max_sky = int(max_sky)
        # if 0 <= max_sky < 2:
        #     weather_total[f'{weather_date[i]}_sky'] = "맑음"
        #     sky[f'{weather_date[i]}'] = "맑음"
        #     pop[i].clear()
        # if 2 <= max_sky < 6:
        #     weather_total[f'{weather_date[i]}_sky'] = "구름많음"
        #     sky[f'{weather_date[i]}'] = "구름많음"
        #     pop[i].clear()
        # if 6 <= max_sky:
        #     weather_total[f'{weather_date[i]}_sky'] = "흐림"
        #     sky[f'{weather_date[i]}'] = "흐림"
        #     pop[i].clear()

    # 일 최저 기온
    for i in range(len(weather_date)):
        for x in items:
            if x['fcstDate'] == weather_date[i] and x["category"] == "TMN":
                weather_total[f'{weather_date[i]}_tmin'] = f"{x['fcstValue']}°C"
                tmin[f'{weather_date[i]}'] = f"{x['fcstValue']}°C"

    # 일 최고 기온
    for i in range(len(weather_date)):
        for x in items:
            if x['fcstDate'] == weather_date[i] and x["category"] == "TMX":
                weather_total[f'{weather_date[i]}_tmax'] = f"{x['fcstValue']}°C"
                tmax[f'{weather_date[i]}'] = f"{x['fcstValue']}°C"

    for i in range(len(weather_date)):
        days.append(f"{weather_date[i][6:8]}일")

    for i in range(len(weather_date)):
        datetime_string = f"{weather_date[i]}"
        datetime_format = "%Y%m%d"
        datetime_result = datetime.datetime.strptime(datetime_string, datetime_format)
        m = datetime_result.month
        d = datetime_result.day
        w = what_day_is_it(datetime_result)
        time.append(f"{m}/{d} ({w})")

    weather = [weather_date, days, time, rainfall, humid, sky, tmin, tmax]

    # with open('./data.json', 'w', encoding='utf-8-sig') as f:
    #     json.dump(weather, f, ensure_ascii=False, indent=4)

    return json.dumps(weather, ensure_ascii=False)


# 상위25, 하위25, 현재 기온, 강수량 추출 함수
def rainfall():
    # 강수량
    df_low = pd.read_csv('data/rainlow10.csv')
    df_max = pd.read_csv('data/rainmax10.csv')

    m = df_max.groupby('month')['cumrain'].apply(lambda grp: grp.nlargest(7).min())
    l = df_low.groupby(['year', 'month'])["cumrain"].max().groupby('month').apply(lambda grp: grp.nlargest(7).min())
    m = m.reindex([10, 11, 12, 1, 2, 3, 4, 5, 6])
    m_2023_4 = m.reindex([10, 11, 12, 1, 2, 3])
    m_2023_4 = list(m_2023_4)
    m = list(m)

    l = l.reindex([10, 11, 12, 1, 2, 3, 4, 5, 6])
    l_2023_4 = l.reindex([10, 11, 12, 1, 2, 3])
    l_2023_4 = list(l_2023_4)
    l = list(l)

    df_2023 = df_low[(df_low['year'] == 2022) | (df_low['year'] == 2023)]
    p_2023 = df_2023.groupby('month')['cumrain'].max()
    p_2023 = p_2023.reindex([10, 11, 12, 1, 2, 3, 4, 5, 6])
    p_2023_4 = p_2023.reindex([10, 11, 12, 1, 2, 3])
    p_2023_4 = list(p_2023_4)
    p_2023 = list(p_2023)

    df_2022 = df_low[(df_low['year'] == 2021) | (df_low['year'] == 2022)]
    p_2022 = df_2022.groupby('month')['cumrain'].max()
    p_2022 = p_2022.reindex([10, 11, 12, 1, 2, 3, 4, 5, 6])
    p_2022 = list(p_2022)

    rainfall_result = {"l": l, "m": m, "m_2023_4": m_2023_4, "p_2023": p_2023, "p_2023_4": p_2023_4,
                       "l_2023_4": l_2023_4, "p_2022": p_2022}

    return rainfall_result


def generate_top_low(a, b):
    # 기온
    df = pd.read_csv("data/wheat_weather.csv")
    df["dd"] = df["datetime"] % 100
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df_top10 = df.groupby("month_day")["tavg"].apply(lambda grp: grp.nlargest(10).min())
    df_bottom10 = df.groupby("month_day")["tavg"].apply(lambda grp: grp.nsmallest(10).max())
    df_avg = df.groupby("month_day")["tavg"].mean()

    content_tavg = []
    content_tmax = []
    content_tmin = []
    content_date = []
    s_date = a
    e_date = b
    for date_idx in pd.date_range(s_date, e_date):  # "2023/6/30"):
        monthday = int(date_idx.strftime("%m%d"))
        date = date_idx.strftime("%Y-%m-%d")
        # print(monthday)
        content_tavg.append(df_avg[monthday])
        content_tmax.append(df_top10[monthday])
        content_tmin.append(df_bottom10[monthday])
        content_date.append(date)

    result = {'tavg': df[(df["timestamp"] >= s_date) & (df["timestamp"] <= e_date)]["tavg"].tolist(),
              'tmax': content_tmax, 'tmin': content_tmin, 'date': content_date}

    return result


app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


db = TinyDB('db.json')
db2 = TinyDB('db_present.json')
db3 = TinyDB('db_future.json')
Station = Query()

r = redis.Redis(host='localhost', port=6379, db=0)

templates = Jinja2Templates(directory="templates")





# 플라스크
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/weather_short/{city}")
# @cross_origin(origin='*')
async def weather_short(city: str):
    # ----발표 날짜( 요청 날짜 , 페이지 열 때? 날짜)
    # KST = datetime.timezone(datetime.timedelta(hours=9))
    # today = datetime.datetime.today().astimezone(KST).strftime("%Y%m%d")  # 오늘날짜
    # date = datetime.datetime.today().astimezone(KST)
        today = datetime.datetime.today().strftime("%Y%m%d")  # 오늘날짜
        date = datetime.datetime.today()
        y = date - datetime.timedelta(days=1)
        yesterday = y.strftime("%Y%m%d")  # 어제날짜
        # ----발표 시각( 요청 시각 , 페이지 열 때? 시간)
        now = datetime.datetime.now()  # 현재 날짜, 시각
        hour = now.hour  # 현재시각

        m = date.month
        d = date.day
        w = what_day_is_it(date)

        # ----요청 시각, 날짜 재조정
        for i in range(8):
            if i * 3 + 2 <= hour < (i + 1) * 3 + 2:
                hour = i * 3 + 2

        if hour < 2:
            hour = 23
            today = yesterday
            m = y.month
            d = y.day
            w = what_day_is_it(y)

        time_hour = f"{hour:02d}" + "00"

        new_param_namwon = {'ServiceKey': serviceKey, 'pageNo': pageNo, 'numOfRows': numOfRaws,
                            'dataType': datatype, 'base_date': today, 'base_time': time_hour, 'nx': nx_namwon,
                            'ny': ny_namwon}

        new_param_iksan = {'ServiceKey': serviceKey, 'pageNo': pageNo, 'numOfRows': numOfRaws,
                           'dataType': datatype, 'base_date': today, 'base_time': time_hour, 'nx': nx_iksan, 'ny': ny_iksan}


        new_param_pyeongchang = {'ServiceKey': serviceKey, 'pageNo': pageNo, 'numOfRows': numOfRaws,
                   'dataType': datatype, 'base_date': today, 'base_time': time_hour, 'nx': nx_pyeongchang, 'ny': nx_pyeongchang}

        new_param_buan = {'ServiceKey': serviceKey, 'pageNo': pageNo, 'numOfRows': numOfRaws,
                          'dataType': datatype, 'base_date': today, 'base_time': time_hour, 'nx': nx_buan, 'ny': nx_buan}

        if city == 'namwon':
            today_weather = db.search((where('name') == "namwon") & (where('date') == today))
        elif city == 'iksan':
            today_weather = db.search((where('name') == "iksan") & (where('date') == today))
        elif city == 'pyeongchang':
            today_weather = db.search((where('name') == "pyeongchang") & (where('date') == today))
        elif city == 'buan':
            today_weather = db.search((where('name') == "buan") & (where('date') == today))
        else:
            today_weather = []

        if len(today_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
            return today_weather[0]['json_content']
        else:
            if city == 'namwon':
                json_content = sky(new_param_namwon)
                db.insert({"name": "namwon", "date": today, "json_content": json_content})
                return json_content
            elif city == "iksan":
                json_content = sky(new_param_iksan)
                db.insert({"name": "iksan", "date": today, "json_content": json_content})
                return json_content
            elif city == "pyeongchang":
                json_content = sky(new_param_pyeongchang)
                db.insert({"name": "pyeongchang", "date": today, "json_content": json_content})
                return json_content
            elif city == "buan":
                json_content = sky(new_param_buan)
                db.insert({"name": "buan", "date": today, "json_content": json_content})
                return json_content
            else:
                return "해당지역없음"


@app.get("/weather_past/{city}")
# @cross_origin(origin='*')
def weather_past(city=str):
    # url3 = "https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionAjax.do"
    # header = {
    #     "Accept": "application/json, text/javascript, */*; q=0.01",
    #     "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    #     "Cache-Control": "no-cache",
    #     "Connection": "keep-alive",
    #     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    #     "Cookie": "XTVID=A230711135728760398; _harry_lang=ko-KR; _harry_fid=hh1197145764; JSESSIONID=CC6ZWZPxhJPbAT4jcugELpg4ucAF38JzKRgpO018w0ii1B7vxoTu1GBB7RUZWCsD.was01_servlet_engine5; _harry_ref=; _harry_url=https^%^3A//data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do^%^3FpgmNo^%^3D179^%^26menuNo^%^3D440^%^26pageIndex^%^3D^%^26minTa^%^3D25.0^%^26stnGroupSns^%^3D^%^26selectType^%^3D1^%^26mddlClssCd^%^3DSFC01^%^26lastDayOfMonth^%^3D31^%^26startDt^%^3D20100101^%^26endDt^%^3D20230724^%^26schType^%^3D1^%^26txtStnNm^%^3D^%^26stnId^%^3D^%^26areaId^%^3D^%^26ureaType^%^3D1^%^26dataFormCd^%^3D2^%^26startYear^%^3D2013^%^26endYear^%^3D2023^%^26tempInputVal^%^3D1^%^26precInputVal^%^3D1^%^26windInputVal^%^3D1^%^26rhmInputVal^%^3D1^%^26icsrInputVal^%^3D1^%^26symbol^%^3D1^%^26inputInt^%^3D^%^26condit^%^3D^%^26symbol2^%^3D1^%^26inputInt2^%^3D^%^26monthCheck^%^3DY^%^26startMonth^%^3D01^%^26endMonth^%^3D12^%^26startDay^%^3D01^%^26endDay^%^3D31^%^26sesn^%^3D1; _harry_hsid=A230725023423777408; _harry_dsid=A230725023423778927; xloc=340X1080",
    #     "Origin": "https ://data.kma.go.kr",
    #     "Pragma": "no-cache",
    #     "Referer": "https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do?curl^%^20^%^22https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionAjax.do^%^22^%^20^^^%^20-H^%^20^%^22Accept:^%^20application/json,^%^20text/javascript,^%^20*/*;^%^20q=0.01^%^22^%^20^^^%^20-H^%^20^%^22Accept-Language:^%^20ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7^%^22^%^20^^^%^20-H^%^20^%^22Cache-Control:^%^20no-cache^%^22^%^20^^^%^20-H^%^20^%^22Connection:^%^20keep-alive^%^22^%^20^^^%^20-H^%^20^%^22Content-Type:^%^20application/x-www-form-urlencoded;^%^20charset=UTF-8^%^22^%^20^^^%^20-H^%^20^%^22Cookie:^%^20XTVID=A230711135728760398;^%^20_harry_lang=ko-KR;^%^20_harry_fid=hh1197145764;^%^20JSESSIONID=CC6ZWZPxhJPbAT4jcugELpg4ucAF38JzKRgpO018w0ii1B7vxoTu1GBB7RUZWCsD.was01_servlet_engine5;^%^20_harry_ref=;^%^20_harry_url=https^^^%^^3A//data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do^^^%^^3FpgmNo^^^%^^3D179^^^%^^26menuNo^^^%^^3D440^^^%^^26pageIndex^^^%^^3D^^^%^^26minTa^^^%^^3D25.0^^^%^^26stnGroupSns^^^%^^3D^^^%^^26selectType^^^%^^3D1^^^%^^26mddlClssCd^^^%^^3DSFC01^^^%^^26lastDayOfMonth^^^%^^3D31^^^%^^26startDt^^^%^^3D20100101^^^%^^26endDt^^^%^^3D20230724^^^%^^26schType^^^%^^3D1^^^%^^26txtStnNm^^^%^^3D^^^%^^26stnId^^^%^^3D^^^%^^26areaId^^^%^^3D^^^%^^26ureaType^^^%^^3D1^^^%^^26dataFormCd^^^%^^3D2^^^%^^26startYear^^^%^^3D2013^^^%^^26endYear^^^%^^3D2023^^^%^^26tempInputVal^^^%^^3D1^^^%^^26precInputVal^^^%^^3D1^^^%^^26windInputVal^^^%^^3D1^^^%^^26rhmInputVal^^^%^^3D1^^^%^^26icsrInputVal^^^%^^3D1^^^%^^26symbol^^^%^^3D1^^^%^^26inputInt^^^%^^3D^^^%^^26condit^^^%^^3D^^^%^^26symbol2^^^%^^3D1^^^%^^26inputInt2^^^%^^3D^^^%^^26monthCheck^^^%^^3DY^^^%^^26startMonth^^^%^^3D01^^^%^^26endMonth^^^%^^3D12^^^%^^26startDay^^^%^^3D01^^^%^^26endDay^^^%^^3D31^^^%^^26sesn^^^%^^3D1;^%^20_harry_hsid=A230725023423777408;^%^20_harry_dsid=A230725023423778927;^%^20xloc=340X1080^%^22^%^20^^^%^20-H^%^20^%^22Origin:^%^20https://data.kma.go.kr^%^22^%^20^^^%^20-H^%^20^%^22Pragma:^%^20no-cache^%^22^%^20^^^%^20-H^%^20^%^22Referer:^%^20https://data.kma.go.kr/climate/RankState/selectRankStatisticsDivisionList.do?pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20100101&endDt=20230724&schType=1&txtStnNm=&stnId=&areaId=&ureaType=1&dataFormCd=2&startYear=2013&endYear=2023&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=12&startDay=01&endDay=31&sesn=1^%^22^%^20^^^%^20-H^%^20^%^22Sec-Fetch-Dest:^%^20empty^%^22^%^20^^^%^20-H^%^20^%^22Sec-Fetch-Mode:^%^20cors^%^22^%^20^^^%^20-H^%^20^%^22Sec-Fetch-Site:^%^20same-origin^%^22^%^20^^^%^20-H^%^20^%^22User-Agent:^%^20Mozilla/5.0^%^20(Linux;^%^20Android^%^206.0;^%^20Nexus^%^205^%^20Build/MRA58N)^%^20AppleWebKit/537.36^%^20(KHTML,^%^20like^%^20Gecko)^%^20Chrome/114.0.0.0^%^20Mobile^%^20Safari/537.36^%^22^%^20^^^%^20-H^%^20^%^22X-Requested-With:^%^20XMLHttpRequest^%^22^%^20^^^%^20-H^%^20^%^22sec-ch-ua:^%^20^^^\^\^^^%^22Not.A/Brand^^^\^\^^^%^22;v=^^^\^\^^^%^228^^^\^\^^^%^22,^%^20^^^\^\^^^%^22Chromium^^^\^\^^^%^22;v=^^^\^\^^^%^22114^^^\^\^^^%^22,^%^20^^^\^\^^^%^22Google^%^20Chrome^^^\^\^^^%^22;v=^^^\^\^^^%^22114^^^\^\^^^%^22^%^22^%^20^^^%^20-H^%^20^%^22sec-ch-ua-mobile:^%^20?1^%^22^%^20^^^%^20-H^%^20^%^22sec-ch-ua-platform:^%^20^^^\^\^^^%^22Android^^^\^\^^^%^22^%^22^%^20^^^%^20--data-raw^%^20^%^22fileType=&pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20100101&endDt=20230724&schType=1&txtStnNm=^^^%^^EB^^^%^^82^^^%^^A8^^^%^^EC^^^%^^9B^^^%^^90&stnId=247&areaId=&ureaType=1&dataFormCd=2&startYear=2013&endYear=2023&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=12&startDay=01&endDay=31&sesn=1",
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "same-origin",
    #     "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    #     "X-Requested-With": "XMLHttpRequest",
    #     "sec-ch-ua": 'Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    #     "sec-ch-ua-mobile": "?1",
    #     "sec-ch-ua-platform": "Android",
    # }
    #
    # if city == "namwon":
    #     param = f"fileType=&pgmNo=179&menuNo=440&pageIndex=&minTa=25.0&stnGroupSns=&selectType=1&mddlClssCd=SFC01&lastDayOfMonth=31&startDt=20000101&endDt=20230724&schType=1&txtStnNm=%EB%82%A8%EC%9B%90&stnId=247&areaId=&ureaType=1&dataFormCd=2&startYear=2022&endYear=2023&tempInputVal=1&precInputVal=1&windInputVal=1&rhmInputVal=1&icsrInputVal=1&symbol=1&inputInt=&condit=&symbol2=1&inputInt2=&monthCheck=Y&startMonth=01&endMonth=06&startDay=01&endDay=30&sesn=1"
    #
    # response = requests.post(url3, headers=header, data=param)
    # result = response.text
    # data = json.loads(result)
    # content = data['data']
    # content_tavg = [x['avgTa'] for x in content]
    # content_tmax = [x['avgDmaxTa'] for x in content]
    # content_tmin = [x['avgDminTa'] for x in content]
    # date = [x['tma'] for x in content]
    #
    # namwon_20 = {'tavg': content_tavg, 'tmax': content_tmax, 'tmin': content_tmin, 'date': date}

    if city == "namwon":
        # 온도
        result_23 = generate_top_low("2022/10/01", "2023/6/30")
        result_22 = generate_top_low("2021/10/01", "2022/6/30")
        result_23_4 = generate_top_low("2022/10/01", "2023/4/10")

        # 강수량
        result_rain = rainfall()

        w = {"result_23": result_23, "result_22": result_22, "result_23_4": result_23_4, "result_rain": result_rain}

        return json.dumps(w, ensure_ascii=False)


@app.get("/weather_now/{city}")
# @cross_origin(origin='*')
def weather_now(city=str):
    KST = datetime.timezone(datetime.timedelta(hours=9))
    time = datetime.datetime.now().astimezone(KST)
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    url4 = "https://www.weather.go.kr/w//renew2021/rest/main/current-weather-obs.do"
    url5 = 'https://www.weather.go.kr/wgis-nuri/aws/buoy?date='

    response = requests.get(url5)
    r_now = response.text
    data_now = json.loads(r_now)
    content = data_now[0]['tm']
    c = datetime.datetime.strptime(content, '%Y%m%d%H%M')
    log = f"(업데이트 {c.month}/{c.day} {c.hour:02d}:{c.minute:02d})"

    response_now = requests.get(url4)
    result_now = response_now.text
    data_now = json.loads(result_now)
    content_now = data_now['data']


    if city == "namwon":
        w_now = [x for x in content_now if x['stnKo'] == '남원']
        w_now[0][
            'now_time'] = f"{time.year}년 {time.month}월 {time.day}일 ({what_day_is_it(time)}) {time.strftime('%H')}:{time.strftime('%M')}"
        w_now[0]['ta'] = w_now[0]['ta'] + "°C"
        w_now[0]['ws'] = w_now[0]['ws'] + "m/s"
        w_now[0]['log'] = log

        w_json = json.dumps(w_now[0], ensure_ascii=False)
    elif city == "buan":
        w_now = [x for x in content_now if x['stnKo'] == '부안']
        w_now[0][
            'now_time'] = f"{time.year}년 {time.month}월 {time.day}일 ({what_day_is_it(time)}) {time.strftime('%H')}:{time.strftime('%M')}"
        w_now[0]['ta'] = w_now[0]['ta'] + "°C"
        w_now[0]['ws'] = w_now[0]['ws'] + "m/s"
        w_now[0]['log'] = log

        w_json = json.dumps(w_now[0], ensure_ascii=False)
    else:
        pass

    # elif city == 'iksan':
    #     iksan_now = [x for x in content_now if x['stnKo'] == '익산']
    #     iksan_now[0][
    #         'now_time'] = f"{time.year}년 {time.month}월 {time.day}일 ({what_day_is_it(time)}) {time.strftime('%H')}:{time.strftime('%M')}"
    #     iksan_now[0]['ta'] = iksan_now[0]['ta'] + "°C"
    #     iksan_now[0]['ws'] = iksan_now[0]['ws'] + "m/s"
    #     iksan_now[0]['log'] = log
    #
    #     iksan_json = json.dumps(iksan_now[0], ensure_ascii=False)
    #     now_weather = db2.search((where('name') == "iksan") & (where('date') == time))
    # else:
    #     now_weather = []

    if city == 'namwon':
        now_weather = db2.search((where('name') == "namwon") & (where('date') == time))
    elif city == 'iksan':
        now_weather = db2.search((where('name') == "buan") & (where('date') == time))
    else:
        now_weather = []

    if len(now_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
        return now_weather[0]['json_content']
    else:
        if city == 'namwon':
            db2.insert({"name": "namwon", "date": date_time, 'json_content': w_json})
            return w_json
        elif city == "buan":
            db2.insert({"name": "buan", "date": date_time, 'json_content': w_json})
            return w_json
        else:
            return "해당지역없음"


def filter_mid(response_land, response_midta):
    time = datetime.datetime.now()
    item_land = response_land.content.decode('utf-8')
    item_midta = response_midta.content.decode('utf-8')

    df_land = json.loads(item_land)
    df_midta = json.loads(item_midta)
    midta_value = df_midta['response']['body']['items']['item']
    land_value = df_land['response']['body']['items']['item']

    weather_mid = {}
    date = []
    name = []
    for i in range(3, 8):
        f = time + datetime.timedelta(days=i)
        t = f.strftime("%Y%m%d")
        name.append(t)
        w = what_day_is_it(f)
        m = f.month
        d = f.day
        date.append(f"{m}/{d} ({w})")
        a = {f'rf_{i}_am': f"{land_value[0][f'rnSt{i}Am']}%", f'rf_{i}_pm': f"{land_value[0][f'rnSt{i}Pm']}%",
             f'wf_{i}_am': f"{land_value[0][f'wf{i}Am']}", f'wf_{i}_pm': f"{land_value[0][f'wf{i}Pm']}",
             f'tamin_{i}': f"{midta_value[0][f'taMin{i}']}°C", f'tamax_{i}': f"{midta_value[0][f'taMax{i}']}°C"}
        weather_mid[t] = a

    weather_mid['date'] = date
    weather_mid['name'] = name

    weather_mid = json.dumps(weather_mid, default=str, ensure_ascii=False)

    return weather_mid

@app.get("/weather_mid/{city}")
# @cross_origin(origin='*')
def weather_mid(city=str):
    # KST = datetime.timezone(datetime.timedelta(hours=9))
    # today = datetime.datetime.now().astimezone(KST).strftime("%Y%m%d")
    # time = datetime.datetime.now().astimezone(KST)
    today = datetime.datetime.now().strftime("%Y%m%d")
    time = datetime.datetime.now()
    y = time - datetime.timedelta(days=1)
    f = datetime.date.today() + datetime.timedelta(days=3)
    yesterday = y.strftime("%Y%m%d")  # 어제날짜

    now = datetime.datetime.now()  # 현재 날짜, 시각
    hour = now.hour  # 현재시각

    # ----요청 시각, 날짜 재조정
    if hour < 6:
        today = yesterday
        time = y

    # 중기육상예보(강수 확률, 날씨 예보)
    url = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
    # 중기기온조희(예상최저, 최고 기온)
    url2 = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'

    # 중기육상예보
    # 전라북도 : 11F10000

    params_url = {
        'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'regId': '11F10000', 'tmFc': f'{today}0600'}

    # regIdd , 중기기온조회
    # 남원 : 11F10401
    # 익산 : 11F10202
    # 평창 : 11D10503
    # 부안 : 21F10602

    params_url_namwon = {
        'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'regId': '11F10401', 'tmFc': f'{today}0600'}

    params_url_iksan = {
        'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'regId': '11F10202', 'tmFc': f'{today}0600'}

    params_url_pyeongchang = {
        'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'regId': '11D10503', 'tmFc': f'{today}0600'}

    params_url_buan = {
        'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'regId': '21F10602', 'tmFc': f'{today}0600'}



    if city == "namwon":
        response_land = requests.get(url, params=params_url_namwon)
        response_midta = requests.get(url2, params=params_url_namwon)
        weather_mid = filter_mid(response_land, response_midta)
    elif city == "iksan":
        response_land = requests.get(url, params=params_url_iksan)
        response_midta = requests.get(url2, params=params_url_iksan)
        weather_mid = filter_mid(response_land, response_midta)
    elif city == "pyeongchang":
        response_land = requests.get(url, params=params_url_pyeongchang)
        response_midta = requests.get(url2, params=params_url_pyeongchang)
        weather_mid = filter_mid(response_land, response_midta)
    elif city == "buan":
        response_land = requests.get(url, params=params_url_buan)
        response_midta = requests.get(url2, params=params_url_buan)
        weather_mid = filter_mid(response_land, response_midta)
    else:
        pass

    if city == 'namwon':
        future_weather = db3.search((where('name') == "namwon") & (where('date') == today))
    elif city == 'iksan':
        future_weather = db3.search((where('name') == "iksan") & (where('date') == today))
    elif city == 'pyeongchang':
        future_weather = db3.search((where('name') == "pyeongchang") & (where('date') == today))
    elif city == 'buan':
        future_weather = db3.search((where('name') == "buan") & (where('date') == today))
    else:
        future_weather = []

    if len(future_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
        return weather_mid
    else:
        if city == 'namwon':
            db3.insert({"name": "namwon", "date": today, 'json_content': weather_mid})
            return weather_mid
        elif city == "iksan":
            db3.insert({"name": "iksan", "date": today, 'json_content': weather_mid})
            return weather_mid
        elif city == "pyeongchang":
            db3.insert({"name": "pyeongchang", "date": today, 'json_content': weather_mid})
            return weather_mid
        elif city == "buan":
            db3.insert({"name": "buan", "date": today, 'json_content': weather_mid})
            return weather_mid
        else:
            return "해당지역없음"


def main():
    # app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    # app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=5000)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == '__main__':
    main()
