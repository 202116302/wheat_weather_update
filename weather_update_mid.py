import datetime
import time
import pandas as pd
import requests
import json

today = datetime.datetime.today().strftime("%Y%m%d")  # 오늘날짜
y = datetime.date.today() - datetime.timedelta(days=1)
f = datetime.date.today() + datetime.timedelta(days=3)
yesterday = y.strftime("%Y%m%d")# 어제날짜
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


df_land = pd.read_json(item_land)
df_midta = pd.read_json(item_midta)
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

# print(weather_mid)


df = pd.read_csv('weather_month.csv', encoding='euc-kr')

print(df)



























