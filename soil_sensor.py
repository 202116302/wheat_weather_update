import requests
import json
import datetime
import pandas as pd
import os
import math

output = '/home/hj5258/wheat_weather_update/sensor_data'
if not os.path.exists(output):
    os.mkdir(output)


def sensor_value(device):
    url = "https://zentracloud.com/api/v3/get_readings/"
    token = "Token {TOKEN}".format(TOKEN="8eb20aa308462c0e8caa33fa341136729ecff542")

    headers = {'content-type': 'application/json', 'Authorization': token}
    end_date = datetime.datetime.today()

    start_date = end_date - datetime.timedelta(days=10)
    page_num = 1
    per_page = 6

    params = {'device_sn': device, 'start_date': start_date, 'end_date': end_date,
              'page_num': page_num, 'per_page': per_page}

    response = requests.get(url, params=params, headers=headers)
    content = json.loads(response.content)
    new_data = {}

    category = ['datetime', 'Logger Temperature', 'Reference Pressure', 'Matric Potential', 'Soil Temperature']
    for i in category:
        if i == 'datetime':
            new_data[f'{i}'] = [content['data']['Logger Temperature'][0]['readings'][x][f'{i}'][:-9] for x in
                                range(per_page)]
        elif i in ['Matric Potential', 'Soil Temperature']:
            for y in range(6):
                new_data[f'{i}_{y + 1}'] = [content['data'][f'{i}'][y]['readings'][x]['value'] for x in range(per_page)]
                if i == 'Matric Potential':
                    new_data[f'{i}_{y + 1}_logdata'] = [
                        round(math.log((content['data'][f'{i}'][y]['readings'][x]['value'] * -1), 10), 2) for x in
                        range(per_page)]
                else:
                    pass
        else:
            new_data[f'{i}'] = [content['data'][f'{i}'][0]['readings'][x]['value'] for x in range(per_page)]

    df = pd.DataFrame(new_data)
    df = df[::-1]
    return df


def main():
    # 'z6-20056' -> 'z6-20061' 교체예정
    device_list = ['z6-20061', 'z6-20051', 'z6-20054', 'z6-20055', 'z6-20058', 'z6-20060', 'z6-20062', 'z6-20063']

    for device in device_list:
        if not os.path.exists(f'{output}/{device}_data.csv'):
            df = sensor_value(device)
            df.to_csv(f'{output}/{device}_data.csv', index=False)
            print(f'{device}_save')
        else:
            pre_df = pd.read_csv(f'{output}/{device}_data.csv')
            new_df = sensor_value(device)
            update_df = pd.concat([pre_df, new_df])
            update_df = update_df.drop_duplicates()
            update_df.to_csv(f'{output}/{device}_data.csv', index=False)
            print(f'{device}_update')


if __name__ == '__main__':
    main()
