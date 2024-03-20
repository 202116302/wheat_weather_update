import uvicorn
import datetime
import requests
from tinydb import TinyDB, where
import pandas as pd
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json

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

templates = Jinja2Templates(directory="templates")






@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/weather_now/{city}")
def weather_now(city=str):
    db_now = TinyDB('forecast_data/db_now.json')
    if city == 'namwon':
        now_weather = db_now.search((where('name') == "namwon"))
    elif city == 'buan':
        now_weather = db_now.search((where('name') == "buan"))
    elif city == 'iksan':
        now_weather = db_now.search((where('name') == "iksan"))
    else:
        now_weather = []

    if len(now_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
        return now_weather[-1]['json_content']
    else:
        return "해당지역없음"


@app.get("/weather_short/{city}")
def weather_short(city=str):
    db_short = TinyDB('forecast_data/db_short.json')
    KST = datetime.timezone(datetime.timedelta(hours=-8))
    date = datetime.datetime.today().astimezone(KST)
    today = date.strftime("%Y%m%d")
    if city == 'namwon':
        today_weather = db_short.search((where('name') == "namwon"))
    elif city == 'iksan':
        today_weather = db_short.search((where('name') == "iksan"))
    elif city == 'pyeongchang':
        today_weather = db_short.search((where('name') == "pyeongchang"))
    elif city == 'buan':
        today_weather = db_short.search((where('name') == "buan"))
    else:
        today_weather = []

    if len(today_weather) > 0:
        return today_weather[-1]['json_content']
    else:
        return "해당지역없음"


@app.get("/weather_mid/{city}")
def weather_mid(city=str):
    db_mid = TinyDB('forecast_data/db_mid.json')
    KST = datetime.timezone(datetime.timedelta(hours=-8))
    date = datetime.datetime.today().astimezone(KST)
    today = date.strftime("%Y%m%d")
    if city == 'namwon':
        future_weather = db_mid.search((where('name') == "namwon"))
    elif city == 'iksan':
        future_weather = db_mid.search((where('name') == "iksan"))
    elif city == 'pyeongchang':
        future_weather = db_mid.search((where('name') == "pyeongchang"))
    elif city == 'buan':
        future_weather = db_mid.search((where('name') == "buan"))
    else:
        future_weather = []

    if len(future_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
        return future_weather[-1]['json_content']
    else:
        return "해당지역없음"


################################# 과거기상 ############################


# 날짜 10월 ~ 6월 추출
def select_date():
    start_date = datetime.datetime(2023, 10, 1)
    end_date = datetime.datetime(2024, 6, 30)

    date_list = []

    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += datetime.timedelta(days=1)

    return date_list


# 기온, 강수량값 딕셔너리 -> 리스트 값으로 변환
def result_tolist(data):
    start_key = '1001'
    end_key = '0630'
    list1 = [round(data[key], 2) for key in data if key >= start_key]
    list2 = [round(data[key], 2) for key in data if key <= end_key]

    list_all = list1 + list2

    return list_all


### 지역별 40년치 기온 상위 25%, 75% ###
@app.get("/past/temp/{city}")
def past_temp(city):
    df = pd.read_csv(f'past_data/{city}_2004_2023.csv')

    df.columns = df.columns.str.strip()

    # 과거 기온
    df2 = df.loc[~df.month.isin([7, 8, 9]), ['year', 'month', 'day', 'tavg', 'rainfall']]

    # zfill -> 자리수 맞춰줌
    df2['date'] = df2['month'].astype(str).str.zfill(2) + df['day'].astype(str).str.zfill(2)

    group_df = df2.groupby('date')

    result = group_df['tavg'].describe()[['25%', '75%']]

    df = pd.read_csv(f'past_data/{city}_2004_2023.csv')
    df.columns = df.columns.str.strip()

    # 현재 기온
    df['date'] = df['year'].astype(str) + df['month'].astype(str).str.zfill(2) + df[
        'day'].astype(str).str.zfill(2)
    df['date'] = pd.to_datetime(df['date'])
    cut_date = pd.to_datetime('2023-10-01')

    cut_today_df = df[df['date'] >= cut_date]
    cut_today_df = cut_today_df.set_index('date', drop=False)
    cut_today_df['date'] = cut_today_df['date'].dt.strftime('%Y-%m-%d')
    result_dict = cut_today_df[['date', 'tavg']].set_index('date').to_dict()['tavg']
    today_value = list(result_dict.values())

    r_25 = result['25%'].to_dict()
    r_75 = result['75%'].to_dict()

    result_dict = {'25%': result_tolist(r_25), '75%': result_tolist(r_75), 'now': today_value, 'date': select_date()}

    return result_dict


### 지역별 특정일자 기온 상위 25%, 75% ###
@app.get("/temp/{date}/{city}")
def past_temp_by_day(city=str, date=str):
    df = pd.read_csv(f'past_data/{city}_2004_2023.csv')

    df.columns = df.columns.str.strip()
    print(df.columns)

    df = df.loc[~df.month.isin([7, 8, 9]), ['year', 'month', 'day', 'tavg', 'rainfall']]

    # df['date'] = df['month'] + df['day']

    # zfill -> 자리수 맞춰줌
    df['date'] = df['month'].astype(str).str.zfill(2) + df['day'].astype(str).str.zfill(2)

    filtered_df = df[df['date'] == date]

    result = filtered_df['tavg'].describe()[['25%', '75%']].to_dict()

    return result


### 지역별 40년치 강수량 상위 25%, 75% ###
@app.get("/past/rainfall/{city}")
def past_rainfall(city=str):
    df = pd.read_csv(f'past_data/{city}_2004_2023.csv')

    df.columns = df.columns.str.strip()
    # print(df.columns)

    df2 = df.loc[~df.month.isin([7, 8, 9]), ['year', 'month', 'day', 'tavg', 'rainfall']]

    rain_df = df2.groupby(['year', 'month'])['rainfall'].sum()
    # print(rain_df)
    rain_df = rain_df.groupby('month')
    # print(rain_df.describe()[['25%', '75%']])

    result = round(rain_df.describe()[['25%', '75%']], 2)
    result = result.reindex([10, 11, 12, 1, 2, 3, 4, 5, 6])

    r_25 = result['25%'].to_dict()
    r_75 = result['75%'].to_dict()

    df['date'] = df['year'].astype(str) + df['month'].astype(str).str.zfill(2) + df[
        'day'].astype(str).str.zfill(2)
    df['date'] = pd.to_datetime(df['date'])
    cut_date = pd.to_datetime('2023-10-01')

    cut_today_df = df[df['date'] >= cut_date]
    cut_today_df = cut_today_df.set_index('date', drop=False)
    # cut_today_df['date'] = cut_today_df['date'].dt.strftime('%Y-%m-%d')

    cut_today_df['end_of_month'] = cut_today_df['date'] + pd.offsets.MonthEnd(0) == cut_today_df['date']

    monthly_rainfall_dict = {}

    for month, group in cut_today_df.groupby('month'):
        if group['end_of_month'].any():
            # sum_rainfall.append(group['rainfall'].sum())
            # sum_rainfall.append({'month': month, 'rainfall_sum': group['rainfall'].sum()})
            monthly_rainfall_sum = round(group['rainfall'].sum(), 2)
            monthly_rainfall_dict[month] = monthly_rainfall_sum

    result_dict = {'25%': list(r_25.values()), '75%': list(r_75.values()), 'now': list(monthly_rainfall_dict.values()),
                   'date': list(r_25.keys())}

    return result_dict


### 지역별 2023-10 ~ 오늘까지 평균 기온  ###
@app.get("/today/temp/{city}")
def loc_today_temp(city=str):
    if city == 'buan':
        num = 243
    elif city == 'iksan':
        num = 146
    else:
        num = 146
    start_year = 2023
    end_year = 2024
    filename = f"past_data/{city}_{start_year}_{end_year}.csv"
    URL = f"https://api.taegon.kr/stations/{146}/?sy={start_year}&ey={end_year}&format=csv"

    res = requests.get(URL)
    with open(filename, "w", newline="") as f:
        f.write(res.text)

    today_df = pd.read_csv(f'past_data/{city}_2023_2024.csv')
    today_df.columns = today_df.columns.str.strip()

    today_df['date'] = today_df['year'].astype(str) + today_df['month'].astype(str).str.zfill(2) + today_df[
        'day'].astype(str).str.zfill(2)
    today_df['date'] = pd.to_datetime(today_df['date'])
    cut_date = pd.to_datetime('2023-10-01')

    cut_today_df = today_df[today_df['date'] >= cut_date]
    cut_today_df = cut_today_df.set_index('date', drop=False)
    cut_today_df['date'] = cut_today_df['date'].dt.strftime('%Y-%m-%d')
    # return cut_today_df['tavg']
    result_dict = cut_today_df[['date', 'tavg']].set_index('date').to_dict()['tavg']
    today_value = list(result_dict.values())
    return today_value


### 지역별 2023-10 ~ 오늘까지 강수량 상위 25%, 75% ###
@app.get("/today/rainfall/{city}")
def loc_today_rainfall(city=str):
    if city == 'buan':
        num = 243
    elif city == 'iksan':
        num = 146
    else:
        num = 146
    start_year = 2023
    end_year = 2024
    filename = f"past_data/{city}_{start_year}_{end_year}.csv"
    URL = f"https://api.taegon.kr/stations/{num}/?sy={start_year}&ey={end_year}&format=csv"

    res = requests.get(URL)
    with open(filename, "w", newline="") as f:
        f.write(res.text)
    today_df = pd.read_csv(f'past_data/{city}_2023_2024.csv')
    today_df.columns = today_df.columns.str.strip()

    today_df['date'] = today_df['year'].astype(str) + today_df['month'].astype(str).str.zfill(2) + today_df[
        'day'].astype(str).str.zfill(2)
    today_df['date'] = pd.to_datetime(today_df['date'])
    cut_date = pd.to_datetime('2023-10-01')

    cut_today_df = today_df[today_df['date'] >= cut_date]
    cut_today_df = cut_today_df.set_index('date', drop=False)
    # cut_today_df['date'] = cut_today_df['date'].dt.strftime('%Y-%m-%d')

    cut_today_df['end_of_month'] = cut_today_df['date'] + pd.offsets.MonthEnd(0) == cut_today_df['date']

    monthly_rainfall_dict = {}

    for month, group in cut_today_df.groupby('month'):
        if group['end_of_month'].any():
            # sum_rainfall.append(group['rainfall'].sum())
            # sum_rainfall.append({'month': month, 'rainfall_sum': group['rainfall'].sum()})
            monthly_rainfall_sum = round(group['rainfall'].sum(), 2)
            monthly_rainfall_dict[month] = monthly_rainfall_sum

    monthly_rainfall = list(monthly_rainfall_dict.values())

    return monthly_rainfall


@app.get("/forecast/{city}")
def load_weather(city=str):
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    now_weather = db_now.search((where('name') == f"{city}"))

    today = datetime.datetime.now().strftime("%Y%m%d")
    today_weather = db_short.search((where('name') == f"{city}"))

    future_weather = db_mid.search((where('name') == f"{city}"))

    data = {'now': now_weather[-1]['json_content'], 'short': today_weather[-1]['json_content'],
            'mid': future_weather[-1]['json_content']}

    return data


############################# 토양수분센서 ###################
## iotplanet
def get_json_file(deviceEui, searchStartDate, searchEndDate):
    url = "http://iotplanet.co.kr/iotplanet/api/v1/rawdata/selectList"

    header = {
        'accept': '*/*',
        'Content-Type': "application/json"
    }

    params = {
        "apiKey": "LvVDkuL95BLo1KL3S2BY317q40mPCkcsz3ocriNQQqwP4MxYeePWuo2yStSLTtNSL",
        "deviceEui": deviceEui,
        "modelIdx": 288,
        "searchStartDate": searchStartDate,
        "searchEndDate": searchEndDate
    }

    response = requests.post(url, headers=header, data=json.dumps(params))
    if response.status_code == 200:  # 성공적인 응답
        data = response.json()  # 응답 데이터를 JSON으로 파싱
        print(response)

        dataMap = data['dataMap']['rawDataList']

        all_df = pd.DataFrame()

        for idx in range(len(dataMap)):
            each_dict = dataMap[idx]
            each_df = pd.DataFrame([each_dict])
            all_df = pd.concat([all_df, each_df])
        all_df = all_df.reset_index()
        all_df = all_df.drop('index', axis=1)

        all_df.to_json('all_df.json', orient='columns')


@app.get('/api/planet/{deviceEui}/{searchStartDate}/{searchEndDate}')
async def test(request: Request, deviceEui, searchStartDate, searchEndDate):
    KST = datetime.timezone(datetime.timedelta(hours=-8))
    date = datetime.datetime.today().astimezone(KST)
    # 대조구4번 광산파
    if deviceEui == 'd4k':
        deviceEui = 'd02544fffefe5bf'
    # 시험구7번 세조파
    elif deviceEui == 's7s':
        deviceEui = 'd02544fffefe59a5'

    if searchStartDate == '1st' and searchEndDate == "today":
        today = date.strftime('%Y-%m-%d %H:%M:%S')
        yeaterday = date - datetime.timedelta(days=1)
        yeaterday = yeaterday.strftime('%Y-%m-%d %H:%M:%S')
        get_json_file(deviceEui, yeaterday, today)
    else:
        get_json_file(deviceEui, searchStartDate, searchEndDate)

    with open('all_df.json', 'r') as json_file:
        json_data = json.load(json_file)
        del json_data['RAW_DATA']
        del json_data['IDX']
        del json_data['PLANET_REGDATE']
        del json_data['LORA_DATE']
        del json_data["DEVICE_EUI"]
        del json_data['INDEX']
        del json_data["DEVICE_NAME"]

        for key, values in json_data.items():
            value_list = []
            for value in values.values():
                value_list.append(value)
            json_data[key] = value_list
    return json_data


## zentra
@app.get("/api/zentra/{divice}")
def load_soilsensor(divice=str):
    df = pd.read_csv(f'sensor_data/{divice}_data.csv')
    df.dropna(inplace=True)
    # 1시간 단위 데이터로 정리
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[df['datetime'].dt.minute == 0]
    for i in range(1, 7):
        df[f"Matric Potential_{i}"] = df[f"Matric Potential_{i}"] * -1

    # 6개 센서 평균(1시간단위) 추가 (토양수분, 지온)
    df['mp_mean'] = df[['Matric Potential_1', 'Matric Potential_2', 'Matric Potential_3','Matric Potential_4','Matric Potential_5','Matric Potential_6']].mean(axis=1)
    df['st_mean'] = df[
        ['Soil Temperature_1', 'Soil Temperature_2', 'Soil Temperature_3', 'Soil Temperature_4', 'Soil Temperature_5',
         'Soil Temperature_6']].mean(axis=1)
    df['mp_mean'] = round(df['mp_mean'], 2)
    df['st_mean'] = round(df['st_mean'], 2)

    # dict 형태로 만들기
    new_dict = df.to_dict()
    for i in df.columns:
        new_dict[f"{i}"] = list(new_dict[f"{i}"].values())


    # 일 단위 데이터 만들기
    df['date'] = df['datetime'].dt.strftime('%Y-%m-%d')
    new_dict['date'] = df['date'].unique().tolist()
    df2 = df.groupby('date').mean()

    df2['mp_mean_d'] = df2[['Matric Potential_1', 'Matric Potential_2', 'Matric Potential_3',
                        'Matric Potential_4', 'Matric Potential_5', 'Matric Potential_6']].mean(
        axis=1)
    df2['st_mean_d'] = df2[
        ['Soil Temperature_1', 'Soil Temperature_2', 'Soil Temperature_3', 'Soil Temperature_4', 'Soil Temperature_5',
         'Soil Temperature_6']].mean(axis=1)

    for i in range(1, 7):
        df2[f'Matric Potential_{i}'] = round(df2[f'Matric Potential_{i}'], 2)
        new_dict[f'Matric Potential_{i}_d'] = df2[f'Matric Potential_{i}'].values.tolist()

    df2['mp_mean_d'] = round(df2['mp_mean_d'], 2)
    df2['st_mean_d'] = round(df2['st_mean_d'], 2)

    new_dict['mp_mean_d'] = df2['mp_mean_d'].values.tolist()
    new_dict['st_mean_d'] = df2['st_mean_d'].values.tolist()

    return new_dict


def main():
    # uvicorn.run(app, host="127.0.0.1", port=5000)
    uvicorn.run(app, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    main()
