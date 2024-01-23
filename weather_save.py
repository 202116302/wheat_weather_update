import json
from collections import Counter
import statistics
import requests
from tinydb import TinyDB, Query, where
import datetime
import os
from tqdm import tqdm

if not os.path.exists('weather_data/'):
    os.mkdir('weather_data/')


db_now = TinyDB('weather_data/db_now.json')
db_short = TinyDB('weather_data/db_short.json')
db_mid = TinyDB('weather_data/db_mid.json')

Station = Query()



##현재기상## city는 한글
def weather_now(city, city_k):
    # KST = datetime.timezone(datetime.timedelta(hours=9))
    # time = datetime.datetime.now().astimezone(KST)
    ## 익산없음 전주로 대체 (20240123)
    if city_k == '익산':
        city_k = '전주'

    time = datetime.datetime.now()
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
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

    new_w = {}
    if city_k in ['남원', '익산', '부안']:
        w_now = [x for x in content_now if x['stnKo'] == f'{city_k}']
        new_w['now_time'] = f"{time.year}년 {time.month}월 {time.day}일 ({what_day_is_it(time)}) {time.strftime('%H')}:{time.strftime('%M')}"
        new_w['ta'] = w_now[0]['ta'] + "°C"
        new_w['ws'] = w_now[0]['ws'] + "m/s"
        new_w['log'] = log
    else:
        pass

    w_json = json.dumps(new_w, ensure_ascii=False)

    now_weather = db_now.search((where('name') == f"{city}") & (where('date') == date_time))

    if city == 'pyeonchang':
        pass
    else:
        if len(now_weather) > 0:
            db_now.update({"name": f"{city}", "date": date_time, 'json_content': w_json})
            return f'{city_k}_업데이트'
        else:
            db_now.insert({"name": f"{city}", "date": date_time, 'json_content': w_json})
            return f'{city_k}_저장성공'




############ 단기예보 API ##################
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

def add_url_params(url, params):
    contents = requests.get(url, params=params)
    items = contents.json().get('response').get('body').get('items').get('item')
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


    return json.dumps(weather, ensure_ascii=False)



## 단기예보 ###
def weather_short(city):
    today = datetime.datetime.today().strftime("%Y%m%d")
    date = datetime.datetime.today()
    y = date - datetime.timedelta(days=1)
    yesterday = y.strftime("%Y%m%d")
    now = datetime.datetime.now()
    hour = now.hour

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


    today_weather = db_short.search((where('name') == f"{city}") & (where('date') == today))


    if len(today_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
        if city == 'namwon':
            json_content = sky(new_param_namwon)
            db_short.update({"name": "namwon", "date": today, "json_content": json_content})
            return json_content
        elif city == "iksan":
            json_content = sky(new_param_iksan)
            db_short.update({"name": "iksan", "date": today, "json_content": json_content})
            return json_content
        elif city == "pyeongchang":
            json_content = sky(new_param_pyeongchang)
            db_short.update({"name": "pyeongchang", "date": today, "json_content": json_content})
            return json_content
        elif city == "buan":
            json_content = sky(new_param_buan)
            db_short.update({"name": "buan", "date": today, "json_content": json_content})
            return json_content
        else:
            return "해당지역없음"
    else:
        if city == 'namwon':
            json_content = sky(new_param_namwon)
            db_short.insert({"name": "namwon", "date": today, "json_content": json_content})
            return json_content
        elif city == "iksan":
            json_content = sky(new_param_iksan)
            db_short.insert({"name": "iksan", "date": today, "json_content": json_content})
            return json_content
        elif city == "pyeongchang":
            json_content = sky(new_param_pyeongchang)
            db_short.insert({"name": "pyeongchang", "date": today, "json_content": json_content})
            return json_content
        elif city == "buan":
            json_content = sky(new_param_buan)
            db_short.insert({"name": "buan", "date": today, "json_content": json_content})
            return json_content
        else:
            return "해당지역없음"

###중기예보###
def weather_mid(city, id):
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

    params_url = {
        'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'regId': f'{id}', 'tmFc': f'{today}0600'}


    response_land = requests.get(url, params=params_url)
    response_midta = requests.get(url2, params=params_url)
    weather_mid = filter_mid(response_land, response_midta)


    future_weather = db_mid.search((where('name') == f"{city}") & (where('date') == today))


    if len(future_weather) > 0:
        db_mid.update({"name": f"{city}", "date": today, 'json_content': weather_mid})
        return weather_mid
    else:
        db_mid.insert({"name": f"{city}", "date": today, 'json_content': weather_mid})



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





def main():
    loc = [('namwon', '남원', '11F10401'),
           ('iksan', '익산', '11F10202'),
           ('buan', '부안', '21F10602'),
           ('pyeongchang', '평창', '11D10503'),]

    for x, y, z in tqdm(loc):
        weather_short(x)
        weather_now(x, y)
        weather_mid(x, z)


if __name__ == '__main__':
    main()
