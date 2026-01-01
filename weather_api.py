#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟天气数据API
模仿中国天气网API
"""

import json
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 机场对应的城市
AIRPORT_CITIES = {
    "PEK": "北京", "PVG": "上海", "CAN": "广州", "SZX": "深圳",
    "CTU": "成都", "CKG": "重庆", "XIY": "西安", "HGH": "杭州",
    "NKG": "南京", "TAO": "青岛", "KMG": "昆明", "CSX": "长沙",
    "WUH": "武汉", "SHE": "沈阳", "TSN": "天津", "URC": "乌鲁木齐"
}

# 天气状况和影响因子
WEATHER_CONDITIONS = {
    "晴": {"code": "00", "impact": 0.0, "icon": "☀️"},
    "多云": {"code": "01", "impact": 0.05, "icon": "⛅"},
    "阴": {"code": "02", "impact": 0.08, "icon": "☁️"},
    "阵雨": {"code": "03", "impact": 0.20, "icon": "🌦️"},
    "雷阵雨": {"code": "04", "impact": 0.40, "icon": "⛈️"},
    "雷阵雨伴有冰雹": {"code": "05", "impact": 0.60, "icon": "🌨️"},
    "雨夹雪": {"code": "06", "impact": 0.50, "icon": "🌧️❄️"},
    "小雨": {"code": "07", "impact": 0.15, "icon": "🌧️"},
    "中雨": {"code": "08", "impact": 0.30, "icon": "🌧️🌧️"},
    "大雨": {"code": "09", "impact": 0.50, "icon": "🌧️🌧️🌧️"},
    "暴雨": {"code": "10", "impact": 0.80, "icon": "🌧️💦"},
    "大暴雨": {"code": "11", "impact": 0.95, "icon": "🌊"},
    "特大暴雨": {"code": "12", "impact": 1.00, "icon": "🌀"},
    "阵雪": {"code": "13", "impact": 0.25, "icon": "🌨️"},
    "小雪": {"code": "14", "impact": 0.20, "icon": "❄️"},
    "中雪": {"code": "15", "impact": 0.40, "icon": "❄️❄️"},
    "大雪": {"code": "16", "impact": 0.60, "icon": "❄️❄️❄️"},
    "暴雪": {"code": "17", "impact": 0.85, "icon": "☃️"},
    "雾": {"code": "18", "impact": 0.35, "icon": "🌫️"},
    "冻雨": {"code": "19", "impact": 0.70, "icon": "🌧️❄️"},
    "沙尘暴": {"code": "20", "impact": 0.90, "icon": "🌪️"},
    "小雨转中雨": {"code": "21", "impact": 0.25, "icon": "🌧️↔️"},
    "中雨转大雨": {"code": "22", "impact": 0.40, "icon": "🌧️🌧️↔️"},
    "大雨转暴雨": {"code": "23", "impact": 0.65, "icon": "🌧️🌧️🌧️↔️"},
    "暴雨转大暴雨": {"code": "24", "impact": 0.88, "icon": "🌧️💦↔️"},
    "大暴雨转特大暴雨": {"code": "25", "impact": 0.98, "icon": "🌊↔️"},
    "浮尘": {"code": "26", "impact": 0.10, "icon": "💨"},
    "扬沙": {"code": "27", "impact": 0.20, "icon": "💨💨"},
    "强沙尘暴": {"code": "28", "impact": 1.00, "icon": "🌪️🌪️"},
    "霾": {"code": "29", "impact": 0.15, "icon": "😷"}
}

def get_seasonal_weather(month, city):
    """根据季节和城市获取典型天气"""
    if month in [12, 1, 2]:  # 冬季
        if city in ["北京", "沈阳", "哈尔滨", "乌鲁木齐"]:
            conditions = ["晴", "多云", "阴", "小雪", "中雪", "雾"]
            temps = range(-15, 5)
        elif city in ["上海", "杭州", "南京"]:
            conditions = ["晴", "多云", "阴", "小雨", "雾"]
            temps = range(0, 10)
        else:  # 南方
            conditions = ["晴", "多云", "阴", "小雨"]
            temps = range(5, 15)
    
    elif month in [3, 4, 5]:  # 春季
        if city in ["北京", "天津", "沈阳"]:
            conditions = ["晴", "多云", "扬沙", "浮尘", "小雨"]
            temps = range(5, 20)
        elif city in ["上海", "南京", "杭州"]:
            conditions = ["晴", "多云", "阴", "小雨", "中雨"]
            temps = range(10, 22)
        else:
            conditions = ["晴", "多云", "小雨", "雷阵雨"]
            temps = range(15, 25)
    
    elif month in [6, 7, 8]:  # 夏季
        if city in ["北京", "天津"]:
            conditions = ["晴", "多云", "雷阵雨", "大雨", "暴雨"]
            temps = range(25, 35)
        elif city in ["上海", "南京", "杭州"]:
            conditions = ["晴", "多云", "雷阵雨", "大雨", "暴雨", "阴"]
            temps = range(28, 38)
        elif city in ["广州", "深圳", "海口"]:
            conditions = ["雷阵雨", "大雨", "暴雨", "多云", "晴"]
            temps = range(28, 35)
        else:
            conditions = ["晴", "多云", "雷阵雨", "中雨"]
            temps = range(25, 33)
    
    else:  # 秋季 9,10,11
        if city in ["北京", "天津", "沈阳"]:
            conditions = ["晴", "多云", "阴", "小雨"]
            temps = range(5, 20)
        elif city in ["上海", "南京", "杭州"]:
            conditions = ["晴", "多云", "阴", "小雨", "中雨"]
            temps = range(10, 25)
        else:
            conditions = ["晴", "多云", "小雨"]
            temps = range(15, 28)
    
    return conditions, temps

@app.route('/api/v1/weather/airport/<airport_code>')
def get_airport_weather(airport_code):
    """获取机场天气"""
    try:
        city = AIRPORT_CITIES.get(airport_code, "北京")
        now = datetime.now()
        month = now.month
        
        # 获取季节性天气
        conditions, temp_range = get_seasonal_weather(month, city)
        condition = random.choice(conditions)
        temp = random.choice(temp_range)
        
        # 根据天气决定其他参数
        weather_info = WEATHER_CONDITIONS.get(condition, WEATHER_CONDITIONS["晴"])
        
        # 生成详细天气数据
        weather_data = {
            "location": {
                "airport": airport_code,
                "city": city,
                "coordinates": {
                    "latitude": round(random.uniform(30.0, 40.0), 4),
                    "longitude": round(random.uniform(110.0, 120.0), 4)
                }
            },
            "current": {
                "temperature": temp,
                "feels_like": temp + random.randint(-3, 2),
                "condition": condition,
                "condition_code": weather_info["code"],
                "icon": weather_info["icon"],
                "humidity": random.randint(30, 90),
                "wind_speed": random.randint(0, 20),
                "wind_direction": random.choice(["北", "东北", "东", "东南", "南", "西南", "西", "西北"]),
                "wind_degrees": random.randint(0, 360),
                "pressure": random.randint(980, 1030),
                "visibility": random.choice(["良好", "一般", "较差", "很差"]),
                "cloud_cover": random.randint(0, 100),
                "uv_index": random.randint(0, 12),
                "precipitation": random.uniform(0, 50) if "雨" in condition or "雪" in condition else 0,
                "last_updated": now.isoformat()
            },
            "flight_impact": {
                "delay_probability": weather_info["impact"],
                "impact_level": get_impact_level(weather_info["impact"]),
                "recommendation": get_weather_recommendation(condition),
                "factors": get_impact_factors(condition)
            }
        }
        
        return jsonify({
            "status": "success",
            "data": weather_data,
            "timestamp": now.isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def get_impact_level(impact):
    """获取影响等级"""
    if impact < 0.1:
        return "无影响"
    elif impact < 0.3:
        return "轻微影响"
    elif impact < 0.6:
        return "中度影响"
    elif impact < 0.8:
        return "严重影响"
    else:
        return "极端影响"

def get_weather_recommendation(condition):
    """获取天气建议"""
    recommendations = {
        "晴": "天气良好，航班正常运行",
        "多云": "天气条件适宜飞行",
        "阴": "天气条件基本正常",
        "小雨": "可能有轻微延误，建议关注航班动态",
        "中雨": "可能造成航班延误，建议提前到达机场",
        "大雨": "高概率延误，建议改签或购买延误险",
        "暴雨": "极可能延误或取消，建议改签",
        "雷阵雨": "可能造成较长时间延误",
        "小雪": "可能有轻微延误",
        "中雪": "可能造成航班延误，机场可能除冰",
        "大雪": "高概率延误或取消",
        "雾": "可能造成航班延误，视能见度情况",
        "雾霾": "可能造成航班延误"
    }
    return recommendations.get(condition, "请关注航班动态")

def get_impact_factors(condition):
    """获取影响因子"""
    factors = []
    
    if "雷" in condition:
        factors.append("雷电可能影响起降")
    if "雨" in condition:
        factors.append("降雨影响能见度")
        if "暴" in condition or "大" in condition:
            factors.append("强降雨可能影响跑道")
    if "雪" in condition:
        factors.append("积雪/结冰影响跑道")
        factors.append("可能需要除冰作业")
    if "雾" in condition:
        factors.append("低能见度影响起降")
    if "沙" in condition or "尘" in condition:
        factors.append("沙尘影响发动机")
        factors.append("低能见度")
    
    if not factors:
        factors.append("天气条件适宜飞行")
    
    return factors

@app.route('/api/v1/weather/forecast/<airport_code>')
def get_weather_forecast(airport_code):
    """获取天气预报"""
    try:
        city = AIRPORT_CITIES.get(airport_code, "北京")
        now = datetime.now()
        month = now.month
        
        forecast = []
        
        for i in range(7):  # 7天预报
            date = now + timedelta(days=i)
            conditions, temp_range = get_seasonal_weather(date.month, city)
            
            # 每天4个时段
            daily_forecast = []
            for hour in [6, 12, 18, 24]:
                condition = random.choice(conditions)
                weather_info = WEATHER_CONDITIONS.get(condition, WEATHER_CONDITIONS["晴"])
                
                daily_forecast.append({
                    "time": f"{hour:02d}:00",
                    "temperature": random.choice(temp_range),
                    "condition": condition,
                    "condition_code": weather_info["code"],
                    "icon": weather_info["icon"],
                    "precipitation_probability": random.randint(0, 100) if "雨" in condition or "雪" in condition else random.randint(0, 30),
                    "wind_speed": random.randint(0, 15),
                    "humidity": random.randint(40, 90)
                })
            
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                "summary": {
                    "max_temp": max([f["temperature"] for f in daily_forecast]),
                    "min_temp": min([f["temperature"] for f in daily_forecast]),
                    "condition": daily_forecast[1]["condition"],  # 中午的天气作为代表
                    "icon": daily_forecast[1]["icon"]
                },
                "hourly": daily_forecast
            })
        
        return jsonify({
            "status": "success",
            "data": {
                "location": {
                    "airport": airport_code,
                    "city": city
                },
                "forecast": forecast,
                "updated": now.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/weather/alert/<airport_code>')
def get_weather_alerts(airport_code):
    """获取天气警报"""
    try:
        city = AIRPORT_CITIES.get(airport_code, "北京")
        now = datetime.now()
        month = now.month
        
        # 根据季节生成可能的警报
        alerts = []
        
        if month in [6, 7, 8]:  # 夏季
            if random.random() < 0.3:
                alerts.append({
                    "type": "暴雨",
                    "level": random.choice(["蓝色", "黄色", "橙色"]),
                    "description": f"{city}市气象台发布暴雨预警",
                    "start_time": now.strftime("%Y-%m-%d %H:%M"),
                    "end_time": (now + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
                    "instructions": "航班可能大面积延误，建议改签",
                    "impact": "高"
                })
            
            if random.random() < 0.2:
                alerts.append({
                    "type": "雷电",
                    "level": "黄色",
                    "description": f"{city}地区有雷电活动",
                    "start_time": now.strftime("%Y-%m-%d %H:%M"),
                    "end_time": (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "instructions": "航班可能暂时无法起降",
                    "impact": "中"
                })
        
        elif month in [12, 1, 2]:  # 冬季
            if random.random() < 0.25:
                alerts.append({
                    "type": "大雾",
                    "level": random.choice(["黄色", "橙色"]),
                    "description": f"{city}市发布大雾预警",
                    "start_time": now.strftime("%Y-%m-%d %H:%M"),
                    "end_time": (now + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
                    "instructions": "能见度低，航班可能延误",
                    "impact": "中"
                })
            
            if random.random() < 0.15:
                alerts.append({
                    "type": "道路结冰",
                    "level": "黄色",
                    "description": f"{city}地区道路结冰预警",
                    "start_time": now.strftime("%Y-%m-%d %H:%M"),
                    "end_time": (now + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
                    "instructions": "机场交通可能受影响",
                    "impact": "低"
                })
        
        if not alerts:
            alerts.append({
                "type": "无预警",
                "level": "正常",
                "description": "当前无天气预警",
                "impact": "无"
            })
        
        return jsonify({
            "status": "success",
            "data": {
                "airport": airport_code,
                "alerts": alerts,
                "updated": now.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("🌤️ 启动模拟天气API服务器...")
    print("🌐 接口地址: http://localhost:8001")
    print("📡 可用接口:")
    print("  GET /api/v1/weather/airport/<机场>      - 机场当前天气")
    print("  GET /api/v1/weather/forecast/<机场>     - 天气预报")
    print("  GET /api/v1/weather/alert/<机场>        - 天气警报")
    
    app.run(host='0.0.0.0', port=8001, debug=False)