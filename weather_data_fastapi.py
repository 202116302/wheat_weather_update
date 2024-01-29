import uvicorn
from datetime import datetime, timedelta
import requests
from tinydb import TinyDB, Query, where
import datetime
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

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

db_now = TinyDB('forecast_data/db_now.json')
db_short = TinyDB('forecast_data/db_short.json')
db_mid = TinyDB('forecast_data/db_mid.json')



@app.get("/weather_now/{city}")
def weather_now(city=str):
    if city == 'namwon':
        now_weather = db_now.search((where('name') == "namwon"))
    elif city == 'buan':
        now_weather = db_now.search((where('name') == "buan"))
    else:
        now_weather = []

    if len(now_weather) > 0:  # 오늘날짜 / 남원 혹은 익산 자료가 있으면, 있는 자료로 리턴
        return now_weather[-1]['json_content']
    else:
        return "해당지역없음"


@app.get("/weather_short/{city}")
def weather_short(city: str):
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
    start_date = datetime(2023, 10, 1)
    end_date = datetime(2024, 6, 30)

    date_list = []

    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

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
@app.get("/{city}/past/temp")
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
@app.get("/{city}/temp/{date}")
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
@app.get("/{city}/past/rainfall")
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


### 지역별 2023-10 ~ 오늘까지 기온 상위 25%, 75% ###
@app.get("/{city}/today/temp")
def loc_today_temp(city=str):
    start_year = 2023
    end_year = 2024
    filename = f"{city}_{start_year}_{end_year}.csv"
    URL = f"https://api.taegon.kr/stations/243/?sy={start_year}&ey={end_year}&format=csv"

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
@app.get("/{city}/today/rainfall")
def loc_today_rainfall(city=str):
    start_year = 2023
    end_year = 2024
    filename = f"{city}_{start_year}_{end_year}.csv"
    URL = f"https://api.taegon.kr/stations/243/?sy={start_year}&ey={end_year}&format=csv"

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

    return monthly_rainfall_dict


@app.get("/{city}/forecast")
def load_weather(city=str):
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    now_weather = db_now.search((where('name') == f"{city}"))

    today = datetime.datetime.now().strftime("%Y%m%d")
    today_weather = db_short.search((where('name') == f"{city}"))

    future_weather = db_mid.search((where('name') == f"{city}"))

    data = {'now': now_weather[-1]['json_content'], 'short': today_weather[-1]['json_content'],
            'mid': future_weather[-1]['json_content']}

    return data


def main():
    # uvicorn.run(app, host="127.0.0.1", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
