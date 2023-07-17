import json

import requests

url = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
url2 = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
params = {'serviceKey': 'HbVUz1YOQ5weklXi+6FnG74Ggi4wiKqvNNncv7HCNL+n4ZuTa3uB4nd3GdcRT9nOzYhlCcvw0cHkz9ZXUelYvQ==',
          'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
          'regId': '11F10401', 'tmFc': '202307170600'}

# regId
# 남원 : 11F10401
# 익산 : 11F10202

response = requests.get(url2, params=params)

text = response.content.decode('utf-8')
print(text)