import json
from collections import Counter
import statistics
import requests
import datetime
from json import dumps
from flask import Flask, request, escape, render_template
from flask_cors import cross_origin
from tinydb import TinyDB, Query, where

# 플라스크 선언
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


db = TinyDB('db.json')
Station = Query()


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



# 지역별 파라미터




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
        humid[f'{weather_date[i]}'] = f"{reh_mean:.1f}"
        pop[i].clear()

    # 하늘 상태 0 ~ 5 맑음 , 6 ~ 8 구름 많음 , 9 ~ 10 흐림
    for i in range(len(weather_date)):
        for x in items:
            if x['fcstDate'] == weather_date[i] and x["category"] == "SKY":
                pop[i].append(x['fcstValue'])

    for i in range(len(weather_date)):
        count_sky = Counter(pop[i])
        sky_max = count_sky.most_common(1)
        max_sky = list(sky_max[0])[0]
        max_sky = int(max_sky)
        if 0 <= max_sky < 6:
            weather_total[f'{weather_date[i]}_sky'] = "맑음"
            sky[f'{weather_date[i]}'] = "맑음"
            pop[i].clear()
        if 6 <= max_sky < 9:
            weather_total[f'{weather_date[i]}_sky'] = "구름많음"
            sky[f'{weather_date[i]}'] = "구름많음"
            pop[i].clear()
        if 9 <= max_sky:
            weather_total[f'{weather_date[i]}_sky'] = "흐림"
            sky[f'{weather_date[i]}'] = "흐림"
            pop[i].clear()

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

    weather = [weather_date, days, rainfall, humid, sky, tmin, tmax]

    # with open('./data.json', 'w', encoding='utf-8-sig') as f:
    #     json.dump(weather, f, ensure_ascii=False, indent=4)

    return json.dumps(weather, ensure_ascii=False)


# 플라스크
@app.route("/")
def home():
    return render_template('landing.html')


@app.route("/weather/<city>")
@app.route("/weather",  methods=['GET'])
@cross_origin(origin='*')
def weather(city=None):
    # ----발표 날짜( 요청 날짜 , 페이지 열 때? 날짜)
    today = datetime.datetime.today().strftime("%Y%m%d")  # 오늘날짜
    y = datetime.date.today() - datetime.timedelta(days=1)
    yesterday = y.strftime("%Y%m%d")  # 어제날짜
    # ----발표 시각( 요청 시각 , 페이지 열 때? 시간)
    now = datetime.datetime.now()  # 현재 날짜, 시각
    hour = now.hour  # 현재시각

    # ----요청 시각, 날짜 재조정
    for i in range(8):
        if i * 3 + 2 <= hour < (i + 1) * 3 + 2:
            hour = i * 3 + 2

    if hour < 2:
        hour = 23
        today = yesterday

    time_hour = f"{hour:02d}" + "00"

    new_param_namwon = {'ServiceKey': serviceKey, 'pageNo': pageNo, 'numOfRows': numOfRaws,
                        'dataType': datatype, 'base_date': today, 'base_time': time_hour, 'nx': nx_namwon,
                        'ny': ny_namwon}

    new_param_iksan = {'ServiceKey': serviceKey, 'pageNo': pageNo, 'numOfRows': numOfRaws,
                       'dataType': datatype, 'base_date': today, 'base_time': time_hour, 'nx': nx_iksan, 'ny': ny_iksan}

    if request.method == 'GET' and city is None:
        city = request.args.get('city')
        city = str(escape(city))

    if city == 'namwon':
        today_weather = db.search((where('name') == "namwon") & (where('date') == today))
    elif city == 'iksan':
        today_weather = db.search((where('name') == "iksan") & (where('date') == today))
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
        else:
            return "해당지역없음"


def main():
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)




if __name__ == '__main__':
    main()
