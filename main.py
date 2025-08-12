import json
from datetime import date
from datetime import datetime, timedelta

from lunardate import LunarDate
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage
import requests
import os
from dotenv import load_dotenv
import sys

# 加载.env文件中的环境变量
load_dotenv()

# 哪天在一起的
start_date = os.environ.get('START_DATE', '2021-01-01')
# 和风天气key
appKey = os.environ.get('APP_KEY', '')
# 生日
birthday = os.environ.get('BIRTHDAY', '01-01')
# 微信公众号的appid和app_secret
app_id = os.environ.get("APP_ID", "")
app_secret = os.environ.get("APP_SECRET", "")
# 微信公众号的user_id,多个用;（分号）隔开
user_ids = os.environ.get("USER_IDS", "")
# 白天模板id
template_id_day = os.environ.get("TEMPLATE_ID_DAY", "")
# 晚上模板id
template_id_night = os.environ.get("TEMPLATE_ID_NIGHT", "")
# 呢称
name = os.environ.get('NAME', '')
# 城市
city = os.environ.get('CITY', '北京')

# 当前时间
today = datetime.now()
# YYYY年MM月DD日
today_date = today.strftime("%Y年%m月%d日")

# 城市ID映射字典
city_ids = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
    "佛山": "101280800",
    # 可以根据需要添加更多城市
}

# 获取城市ID，如果城市不在字典中则使用城市名称
city_id_or_name = city_ids.get(city, city)

# 构建请求体
headers = {"Content-Type": "application/x-www-form-urlencoded",
           "X-QW-Api-Key": appKey}
           
# 使用用户提供的API Host
api_host = "https://pj5khuxkcq.re.qweatherapi.com"

# 初始化参数
params = {
    "location": city_id_or_name
}

# 尝试多种方式获取城市ID和天气数据
city_id = None
realtime_json = None
day_forecast_json = None

# 首先尝试直接获取天气数据（因为这已经被验证是有效的）
print("尝试直接获取天气数据...")
weather_url = f"{api_host}/v7/weather/now"
weather_params = {"location": city_id_or_name}
weather_headers = {"Content-Type": "application/x-www-form-urlencoded", "X-QW-Api-Key": appKey}
weather_response = requests.get(weather_url, params=weather_params, headers=weather_headers)
print(f"直接天气API响应状态码: {weather_response.status_code}")

if weather_response.status_code == 200:
    print("直接获取天气数据成功")
    try:
        realtime_json = weather_response.json()
        # 设置城市ID为查询用的ID
        city_id = city_id_or_name
    except json.JSONDecodeError as e:
        print(f"无法解析直接天气API响应: {e}")
        print(f"响应内容: {weather_response.text}")
        sys.exit(1)
else:
    # 如果直接获取失败，尝试通过城市查询获取城市ID
    print("直接获取天气数据失败，尝试通过城市查询获取城市ID...")
    url = f"{api_host}/v2/city/lookup"
    print(f"正在请求城市信息: {url}")
    print(f"请求头: {headers}")
    print(f"请求参数: {params}")
    response = requests.get(url, params=params, headers=headers)
    print(f"城市信息API响应状态码: {response.status_code}")
    print(f"完整URL: {response.url}")

    # 检查HTTP响应状态码
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        # 尝试不同的API端点和认证方式
        print("尝试使用devapi.qweather.com和参数认证...")
        fallback_url = f"https://devapi.qweather.com/v2/city/lookup"
        fallback_params = {"location": city_id_or_name, "key": appKey}
        fallback_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        print(f"备用请求URL: {fallback_url}")
        print(f"备用请求参数: {fallback_params}")
        fallback_response = requests.get(fallback_url, params=fallback_params, headers=fallback_headers)
        print(f"备用API响应状态码: {fallback_response.status_code}")
        
        if fallback_response.status_code == 200:
            response = fallback_response
            print("备用API请求成功，继续执行...")
        else:
            print("所有尝试都失败了，请检查APP_KEY是否正确配置以及网络连接")
            sys.exit(1)

    try:
        resp_json = response.json()
    except json.JSONDecodeError as e:
        print(f"无法解析城市信息API响应: {e}")
        print(f"响应内容: {response.text}")
        print("请检查APP_KEY是否正确配置以及网络连接")
        sys.exit(1)

    # 检查返回数据结构
    if "code" in resp_json and resp_json["code"] != "200":
        print(f"API返回错误，错误码: {resp_json.get('code')}")
        print(f"错误信息: {resp_json.get('message', '未知错误')}")
        sys.exit(1)
        
    if "location" not in resp_json or not resp_json["location"]:
        print("无法找到指定城市，请检查CITY配置是否正确")
        sys.exit(1)
        
    city_id = resp_json["location"][0]["id"]

# 现在我们有了城市ID，获取实时天气数据
if realtime_json is None:
    # 如果还没有获取实时天气数据，则获取
    url = f"{api_host}/v7/weather/now"
    params = {"location": city_id}
    print(f"正在请求实时天气: {url}")
    response = requests.get(url, params=params, headers=headers)
    print(f"实时天气API响应状态码: {response.status_code}")

    # 检查HTTP响应状态码
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        print("请检查APP_KEY是否正确配置以及网络连接")
        sys.exit(1)

    try:
        realtime_json = response.json()
    except json.JSONDecodeError as e:
        print(f"无法解析实时天气API响应: {e}")
        print(f"响应内容: {response.text}")
        print("请检查APP_KEY是否正确配置以及网络连接")
        sys.exit(1)

# 检查返回数据结构
if "code" in realtime_json and realtime_json["code"] != "200":
    print(f"API返回错误，错误码: {realtime_json.get('code')}")
    print(f"错误信息: {realtime_json.get('message', '未知错误')}")
    sys.exit(1)

# 实时天气状况
if "now" not in realtime_json:
    print("实时天气数据获取失败，请检查APP_KEY是否正确配置")
    sys.exit(1)

realtime = realtime_json["now"]
# 当前温度 拼接 当前天气
now_temperature = realtime["temp"] + "°C " + realtime["text"]
# 添加调试信息
print(f"实时天气数据: {realtime}")
print(f"当前温度值: {now_temperature}")

# 根据城市地理位置获取3天天气状况
url = f"{api_host}/v7/weather/3d"
params = {"location": city_id}
print(f"正在请求天气预报: {url}")
response = requests.get(url, params=params, headers=headers)
print(f"天气预报API响应状态码: {response.status_code}")

# 检查HTTP响应状态码
if response.status_code != 200:
    print(f"请求失败，状态码: {response.status_code}")
    print("请检查APP_KEY是否正确配置以及网络连接")
    sys.exit(1)

try:
    day_forecast_json = response.json()
except json.JSONDecodeError as e:
    print(f"无法解析天气预报API响应: {e}")
    print(f"响应内容: {response.text}")
    print("请检查APP_KEY是否正确配置以及网络连接")
    sys.exit(1)

# 检查返回数据结构
if "code" in day_forecast_json and day_forecast_json["code"] != "200":
    print(f"API返回错误，错误码: {day_forecast_json.get('code')}")
    print(f"错误信息: {day_forecast_json.get('message', '未知错误')}")
    sys.exit(1)

# -----------------------今天天气状况-----------------------------
# 天气状况
day_forecast_today = day_forecast_json["daily"][0]
# 日出时间
day_forecast_today_sunrise = day_forecast_today["sunrise"]
# 日落时间
day_forecast_today_sunset = day_forecast_today["sunset"]
# 天气
day_forecast_today_weather = day_forecast_today["textDay"]
# 最低温度
day_forecast_today_temperature_min = day_forecast_today["tempMin"]+"℃"
# 最高温度
day_forecast_today_temperature_max = day_forecast_today["tempMax"]+"℃"
# 夜间天气
day_forecast_today_night = day_forecast_today["textNight"]
# 白天风向
day_forecast_today_windDirDay = day_forecast_today["windDirDay"]
# 夜间风向
day_forecast_today_windDirNight = day_forecast_today["windDirNight"]
# 风力等级
day_forecast_today_windScaleDay = day_forecast_today["windScaleDay"]
# -----------------------今天天气状况-----------------------------


# -----------------------明天天气状况-----------------------------
# 天气状况
day_forecast_tomorrow = day_forecast_json["daily"][1]
# 天气
day_forecast_tomorrow_weather = day_forecast_tomorrow["textDay"]
# 日出时间
day_forecast_tomorrow_sunrise = day_forecast_tomorrow["sunrise"]
# 日落时间
day_forecast_tomorrow_sunset = day_forecast_tomorrow["sunset"]
# 最低温度
day_forecast_tomorrow_temperature_min = day_forecast_tomorrow["tempMin"] + "℃"
# 最高温度
day_forecast_tomorrow_temperature_max = day_forecast_tomorrow["tempMax"] + "℃"
# 夜间天气
day_forecast_tomorrow_night = day_forecast_today["textNight"]
# 白天风向
day_forecast_tomorrow_windDirDay = day_forecast_today["windDirDay"]
# 夜间风向
day_forecast_tomorrow_windDirNight = day_forecast_today["windDirNight"]
# 风力等级
day_forecast_tomorrow_windScaleDay = day_forecast_today["windScaleDay"]
# -----------------------明天天气状况-----------------------------


# -----------------------后天天气状况-----------------------------
# 天气状况
day_forecast_T2 = day_forecast_json["daily"][2]
# 天气
day_forecast_T2_textDay = day_forecast_T2["textDay"]
# 最低温度
day_forecast_T2_temperature_min = day_forecast_T2["tempMin"] + "℃"
# 最高温度
day_forecast_T2_temperature_max = day_forecast_T2["tempMax"] + "℃"
# -----------------------后天天气状况-----------------------------


# 距离春节还有多少天
def days_until_spring_festival(year=None):
    """
    计算距离下一个春节还有多少天。
    如果未提供年份，则默认为当前年份。
    """
    if year is None:
        year = datetime.now().year  # 获取当前年份

    # 获取当年春节的日期（农历正月初一转换为公历）
    spring_festival_lunar = LunarDate(year, 1, 1)
    spring_festival_solar = spring_festival_lunar.toSolarDate()

    # 获取当前日期
    today = datetime.now().date()

    # 计算差值，注意需要将日期转换为同类型的对象才能相减
    days_until = (spring_festival_solar - today).days

    # 如果春节已经过去，则计算到下一年的春节
    if days_until <= 0:
        days_until = days_until_spring_festival(year + 1)

    return days_until


# 在一起多天计算
def get_count():
    delta = today - datetime.strptime(start_date, "%Y-%m-%d")
    return delta.days+1


# 生日计算
def get_birthday():
    next = datetime.strptime(str(date.today().year) + "-" + birthday, "%Y-%m-%d")
    if next < datetime.now():
      next = next.replace(year=next.year + 1)
    return (next - today).days


# 彩虹屁接口
def get_words():
    words = requests.get("https://api.shadiao.pro/chp")
    if words.status_code != 200:
        return get_words()
    text = words.json()['data']['text']

    # 按照20个字符分割字符串
    chunk_size = 20
    split_notes = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    # 分配note N 如果split_notes元素少于5，则用空字符串填充
    [note1, note2, note3, note4, note5] = (split_notes + [""] * 5)[:5]
    return note1, note2, note3, note4, note5


if __name__ == '__main__':
    # 获取微信客户端
    client = WeChatClient(app_id, app_secret)

    # 获取微信模板消息接口
    wm = WeChatMessage(client)

    # 获取彩虹屁
    note1, note2, note3, note4, note5 = get_words()

    # 获取当前UTC时间
    now_utc = datetime.utcnow()
    # 转换为北京时间（UTC+8）
    beijing_time = now_utc + timedelta(hours=8)
    # 获取当前小时数
    hour_of_day = beijing_time.hour
    # 默认发当天
    strDay = "today"
    # 如果当前时间大于15点，也就是晚上，则发送明天天气
    if hour_of_day > 15:
        strDay = "tomorrow"
        template_id_day = template_id_night

    print("当前时间：" + str(beijing_time)+"即将推送："+strDay+"信息")

    data = {"name": {"value": name},
            "today": {"value": today_date},
            "city": {"value": city},
            "weather": {"value": globals()[f'day_forecast_{strDay}_weather']},
            "now_temperature": {"value": now_temperature},
            "min_temperature": {"value": globals()[f'day_forecast_{strDay}_temperature_min']},
            "max_temperature": {"value": globals()[f'day_forecast_{strDay}_temperature_max']},
            "love_date": {"value": get_count()},
            "birthday": {"value": get_birthday()},
            "diff_date1": {"value": days_until_spring_festival()},
            "sunrise": {"value": globals()[f'day_forecast_{strDay}_sunrise']},
            "sunset": {"value": globals()[f'day_forecast_{strDay}_sunset']},
            "textNight": {"value": globals()[f'day_forecast_{strDay}_night']},
            "windDirDay": {"value": globals()[f'day_forecast_{strDay}_windDirDay']},
            "windDirNight": {"value": globals()[f'day_forecast_{strDay}_windDirNight']},
            "windScaleDay": {"value": globals()[f'day_forecast_{strDay}_windScaleDay']},
            "note1": {"value": note1},
            "note2": {"value": note2},
            "note3": {"value": note3},
            "note4": {"value": note4},
            "note5": {"value": note5}
            }
    # print(data)

    # 拆分user_ids
    user_ids = user_ids.split(";")
    for e in user_ids:
        res = wm.send_template(e, template_id_day, data)
        print(res)