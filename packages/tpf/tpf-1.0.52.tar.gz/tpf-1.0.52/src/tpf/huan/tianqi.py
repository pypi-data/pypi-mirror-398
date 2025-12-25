



import requests  
import time
import os
  
def fetch_weather(city_name, api_key):  
    """使用OpenWeatherMap API获取指定城市的天气信息
      
    参数:  
    -------------------
    - city_name (str): 城市名称  
    - api_key (str): OpenWeatherMap API密钥  
      
    返回: 
    ----------------------
    - dict: 包含天气信息的字典  
    """  
    # OpenWeatherMap API URL  
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"  
      
    # 发送GET请求  
    response = requests.get(url)  
      
    # 检查请求是否成功  
    if response.status_code == 200:  
        # 解析JSON响应  
        weather_data = response.json()  
          
        # 提取并返回关键信息  
        return {  
            'city': weather_data['name'],  
            'temperature': weather_data['main']['temp'],  
            'description': weather_data['weather'][0]['description'],  
            'humidity': weather_data['main']['humidity'],  
            'pressure': weather_data['main']['pressure']  
        }  
    else:  
        return None  


def weather_city(city_name = 'Beijing'):

    # 示例：获取北京的天气  
    api_key = '7b2ee2a4289471dd639fbeea5af0f75d'  
    weather_info = fetch_weather(city_name, api_key) 
      
    if weather_info:  
        # print(f"城市: {weather_info['city']}")  
        # print(f"温度: {weather_info['temperature']}°C")  
        # print(f"天气状况: {weather_info['description']}")  
        # print(f"湿度: {weather_info['humidity']}%")  
        # print(f"气压: {weather_info['pressure']} hPa") 
        weather_info["get_time"] = time.strftime("%Y-%m-%d %H:%M") 
    else:  
        print("无法获取天气信息")
    return weather_info


import pandas as pd

def append_csv(new_data, file_path):
    """追加写csv文件，适合小数据量

    """
    if os.path.exists(file_path):
        # 读取现有的 CSV 文件
        existing_df = pd.read_csv(file_path)

        # 将新数据追加到现有的 DataFrame
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
    else:
        updated_df = new_data

    # 将更新后的 DataFrame 写回到 CSV 文件
    updated_df.to_csv(file_path, index=False)



def tianqi_citys(city_list = ['Beijing','Tianjin','Hebei'],file_path="tianqi_record.csv"):
    """获取指定城市的天气预报
    """
    for city in city_list:
        weather_info = weather_city(city_name = city)
        df = pd.DataFrame(weather_info,index=[0])
        append_csv(df,file_path=file_path)
    