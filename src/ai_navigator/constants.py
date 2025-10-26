"""
Constants and configuration values for AI Navigator.

This module contains all hardcoded values extracted from the main program
to improve maintainability and reduce code duplication.
"""

from typing import Dict

DEFAULT_LOCATION = {
    "name": "北京市",
    "longitude": 116.4074,
    "latitude": 39.9042,
    "formatted_address": "中国北京市"
}

CITY_TRANSLATIONS = {
    "Guangzhou": "广州",
    "Beijing": "北京",
    "Shanghai": "上海",
    "Shenzhen": "深圳",
    "Hangzhou": "杭州",
    "Chengdu": "成都",
    "Wuhan": "武汉",
    "Xi'an": "西安",
    "Chongqing": "重庆",
    "Nanjing": "南京"
}

REGION_TRANSLATIONS = {
    "Guangdong": "广东",
    "Beijing": "北京",
    "Shanghai": "上海",
    "Zhejiang": "浙江",
    "Sichuan": "四川",
    "Hubei": "湖北",
    "Shaanxi": "陕西",
    "Chongqing": "重庆",
    "Jiangsu": "江苏"
}

COUNTRY_TRANSLATIONS = {
    "CN": "中国",
    "US": "美国",
    "JP": "日本",
    "KR": "韩国",
    "SG": "新加坡"
}

CURRENT_LOCATION_KEYWORDS = [
    "当前位置",
    "我的位置",
    "current location",
    "Current Location",
    "这里",
    "此地"
]

GPS_PARAM_OPTIONS = [
    {"address": "current_location"},
    {"address": ""},
    {"get_current_location": True}
]

NAVIGATION_STEPS = {
    "CONNECT": 1,
    "PARSE": 2,
    "START_COORDS": 3,
    "END_COORDS": 4,
    "OPEN_BROWSER": 5,
    "TOTAL": 5
}

def get_step_label(step_name: str) -> str:
    """Get formatted step label for progress display."""
    step_num = NAVIGATION_STEPS.get(step_name)
    total = NAVIGATION_STEPS["TOTAL"]
    return f"[{step_num}/{total}]" if step_num else ""
