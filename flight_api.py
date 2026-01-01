#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟航班数据API
模仿航旅纵横/飞常准API接口
"""

import json
import random
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 模拟的航空公司数据
AIRLINES = {
    "CA": {"name": "中国国际航空", "iata": "CA", "icao": "CCA", "callsign": "AIR CHINA"},
    "MU": {"name": "中国东方航空", "iata": "MU", "icao": "CES", "callsign": "CHINA EASTERN"},
    "CZ": {"name": "中国南方航空", "iata": "CZ", "icao": "CSN", "callsign": "CHINA SOUTHERN"},
    "HU": {"name": "海南航空", "iata": "HU", "icao": "CHH", "callsign": "HAINAN"},
    "ZH": {"name": "深圳航空", "iata": "ZH", "icao": "CSZ", "callsign": "SHENZHEN AIR"},
    "MF": {"name": "厦门航空", "iata": "MF", "icao": "CXA", "callsign": "XIAMEN AIR"},
    "HO": {"name": "吉祥航空", "iata": "HO", "icao": "DKH", "callsign": "AIR JUNEYAO"},
    "9C": {"name": "春秋航空", "iata": "9C", "icao": "CQH", "callsign": "AIR SPRING"},
    "KN": {"name": "中国联合航空", "iata": "KN", "icao": "CUA", "callsign": "LIANHANG"},
    "GS": {"name": "天津航空", "iata": "GS", "icao": "GCR", "callsign": "BOHAI"}
}

# 中国主要机场
AIRPORTS = {
    "PEK": {"iata": "PEK", "icao": "ZBAA", "name": "北京首都国际机场", "city": "北京", "country": "CN"},
    "PVG": {"iata": "PVG", "icao": "ZSPD", "name": "上海浦东国际机场", "city": "上海", "country": "CN"},
    "CAN": {"iata": "CAN", "icao": "ZGGG", "name": "广州白云国际机场", "city": "广州", "country": "CN"},
    "SZX": {"iata": "SZX", "icao": "ZGSZ", "name": "深圳宝安国际机场", "city": "深圳", "country": "CN"},
    "CTU": {"iata": "CTU", "icao": "ZUUU", "name": "成都天府国际机场", "city": "成都", "country": "CN"},
    "CKG": {"iata": "CKG", "icao": "ZUCK", "name": "重庆江北国际机场", "city": "重庆", "country": "CN"},
    "XIY": {"iata": "XIY", "icao": "ZLXY", "name": "西安咸阳国际机场", "city": "西安", "country": "CN"},
    "HGH": {"iata": "HGH", "icao": "ZSHC", "name": "杭州萧山国际机场", "city": "杭州", "country": "CN"},
    "NKG": {"iata": "NKG", "icao": "ZSNJ", "name": "南京禄口国际机场", "city": "南京", "country": "CN"},
    "TAO": {"iata": "TAO", "icao": "ZSQD", "name": "青岛胶东国际机场", "city": "青岛", "country": "CN"}
}

# 模拟航班数据缓存
flight_cache = {}

def generate_flight_data(flight_number, date):
    """生成航班数据"""
    airline_code = flight_number[:2]
    
    # 获取或创建航班信息
    if flight_number not in flight_cache:
        # 随机选择出发和到达机场
        airports = list(AIRPORTS.keys())
        origin = random.choice(airports)
        destination = random.choice([a for a in airports if a != origin])
        
        # 航班基础信息
        flight_info = {
            "flight_number": flight_number,
            "airline": AIRLINES.get(airline_code, {"name": "未知航空"}),
            "aircraft_type": random.choice(["B737", "A320", "A330", "B787", "A350"]),
            "registration": f"B-{random.randint(1000, 9999)}",
            "origin": AIRPORTS[origin],
            "destination": AIRPORTS[destination],
            "scheduled_departure": f"{date} {random.randint(6, 22):02d}:{random.randint(0, 59):02d}",
            "scheduled_arrival": f"{date} {random.randint(8, 23):02d}:{random.randint(0, 59):02d}",
            "actual_departure": None,
            "actual_arrival": None,
            "departure_terminal": random.choice(["T1", "T2", "T3"]),
            "arrival_terminal": random.choice(["T1", "T2", "T3"]),
            "departure_gate": f"Gate {chr(65 + random.randint(0, 8))}{random.randint(1, 50)}",
            "arrival_gate": f"Gate {chr(65 + random.randint(0, 8))}{random.randint(1, 50)}",
            "status": "计划",
            "delay_minutes": 0,
            "baggage_claim": random.choice(["1", "2", "3", "4", "5"]),
            "checkin_counters": f"{random.randint(1, 50)}-{random.randint(51, 100)}",
            "distance": random.randint(500, 3000),
            "duration": random.randint(60, 240)
        }
        
        flight_cache[flight_number] = flight_info
    
    return flight_cache[flight_number]

def update_flight_status(flight_data):
    """更新航班状态（模拟实时变化）"""
    current_hour = datetime.now().hour
    
    # 基于时间的状态变化
    scheduled_time = datetime.strptime(flight_data["scheduled_departure"], "%Y-%m-%d %H:%M")
    time_diff = (scheduled_time - datetime.now()).total_seconds() / 60  # 分钟
    
    if time_diff > 180:  # 3小时前
        status = "计划"
        delay = 0
    elif time_diff > 120:  # 2小时前
        status = "值机开放"
        delay = 0
    elif time_diff > 60:  # 1小时前
        status = "值机中"
        # 20%概率延误
        delay = random.randint(15, 45) if random.random() < 0.2 else 0
    elif time_diff > 30:  # 30分钟前
        status = "登机中"
        # 30%概率延误
        delay = random.randint(30, 90) if random.random() < 0.3 else 0
    elif time_diff > 0:  # 起飞前
        status = "起飞"
        # 40%概率延误
        delay = random.randint(45, 120) if random.random() < 0.4 else 0
    else:
        status = "到达"
        delay = flight_data.get("delay_minutes", 0)
    
    # 更新数据
    flight_data["status"] = status
    flight_data["delay_minutes"] = delay
    
    # 更新实际时间（如果有延误）
    if delay > 0 and status in ["登机中", "起飞", "到达"]:
        scheduled_dt = datetime.strptime(flight_data["scheduled_departure"], "%Y-%m-%d %H:%M")
        actual_dt = scheduled_dt + timedelta(minutes=delay)
        flight_data["actual_departure"] = actual_dt.strftime("%Y-%m-%d %H:%M")
        
        # 到达时间也相应延迟
        scheduled_arrival = datetime.strptime(flight_data["scheduled_arrival"], "%Y-%m-%d %H:%M")
        actual_arrival = scheduled_arrival + timedelta(minutes=delay)
        flight_data["actual_arrival"] = actual_arrival.strftime("%Y-%m-%d %H:%M")
    
    return flight_data

# ========== API接口 ==========

@app.route('/api/v1/flight/<flight_number>')
def get_flight_info(flight_number):
    """获取航班信息（模仿航旅纵横API）"""
    try:
        # 获取日期参数
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # 生成航班数据
        flight_data = generate_flight_data(flight_number, date)
        
        # 更新状态
        flight_data = update_flight_status(flight_data)
        
        # 构建响应
        response = {
            "status": "success",
            "data": {
                "flight": {
                    "number": flight_data["flight_number"],
                    "iata": flight_number,
                    "icao": f"{flight_number[:2]}{random.randint(100, 999)}",
                    "airline": flight_data["airline"],
                    "aircraft": {
                        "type": flight_data["aircraft_type"],
                        "registration": flight_data["registration"]
                    }
                },
                "departure": {
                    "airport": flight_data["origin"],
                    "scheduled": flight_data["scheduled_departure"],
                    "estimated": flight_data.get("actual_departure", flight_data["scheduled_departure"]),
                    "terminal": flight_data["departure_terminal"],
                    "gate": flight_data["departure_gate"],
                    "checkin": flight_data["checkin_counters"]
                },
                "arrival": {
                    "airport": flight_data["destination"],
                    "scheduled": flight_data["scheduled_arrival"],
                    "estimated": flight_data.get("actual_arrival", flight_data["scheduled_arrival"]),
                    "terminal": flight_data["arrival_terminal"],
                    "gate": flight_data["arrival_gate"],
                    "baggage": flight_data["baggage_claim"]
                },
                "status": {
                    "text": flight_data["status"],
                    "code": get_status_code(flight_data["status"]),
                    "delay": flight_data["delay_minutes"],
                    "updated": datetime.now().isoformat()
                },
                "flight_info": {
                    "distance": flight_data["distance"],
                    "duration": flight_data["duration"],
                    "seats": random.randint(100, 300),
                    "load_factor": random.randint(60, 95)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def get_status_code(status_text):
    """获取状态代码"""
    status_codes = {
        "计划": "S",
        "值机开放": "CI",
        "值机中": "CI",
        "登机中": "BD",
        "起飞": "DP",
        "到达": "AR",
        "取消": "CX",
        "延误": "DL"
    }
    return status_codes.get(status_text, "UN")

@app.route('/api/v1/flight/<flight_number>/history')
def get_flight_history(flight_number):
    """获取航班历史数据（模仿飞常准API）"""
    try:
        days = int(request.args.get('days', 7))
        
        history = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 生成历史数据
            flight_data = generate_flight_data(flight_number, date)
            
            # 模拟历史延误
            delay_prob = random.random()
            if delay_prob < 0.3:
                delay = 0
                status = "准点"
            elif delay_prob < 0.7:
                delay = random.randint(5, 30)
                status = "轻微延误"
            else:
                delay = random.randint(30, 120)
                status = "延误"
            
            history.append({
                "date": date,
                "flight_number": flight_number,
                "route": f"{flight_data['origin']['iata']}-{flight_data['destination']['iata']}",
                "scheduled_departure": flight_data["scheduled_departure"],
                "actual_departure": flight_data.get("actual_departure", flight_data["scheduled_departure"]),
                "delay_minutes": delay,
                "status": status,
                "aircraft": flight_data["aircraft_type"],
                "load_factor": random.randint(60, 95)
            })
        
        return jsonify({
            "status": "success",
            "data": {
                "flight": flight_number,
                "history": history,
                "stats": {
                    "total_flights": days,
                    "on_time": len([h for h in history if h["delay_minutes"] <= 15]),
                    "delayed": len([h for h in history if h["delay_minutes"] > 15]),
                    "avg_delay": sum(h["delay_minutes"] for h in history) / days,
                    "max_delay": max(h["delay_minutes"] for h in history)
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/flights/airport/<airport_code>')
def get_airport_flights(airport_code):
    """获取机场航班动态"""
    try:
        flight_type = request.args.get('type', 'departures')  # departures/arrivals
        limit = int(request.args.get('limit', 20))
        
        flights = []
        
        for i in range(limit):
            # 生成航班号
            airlines = list(AIRLINES.keys())
            airline = random.choice(airlines)
            flight_num = f"{airline}{random.randint(1000, 9999)}"
            
            # 确定机场
            if flight_type == 'departures':
                origin = AIRPORTS.get(airport_code, {"iata": airport_code, "name": f"{airport_code}机场"})
                airports_list = [a for a in AIRPORTS.keys() if a != airport_code]
                dest_code = random.choice(airports_list) if airports_list else "PVG"
                destination = AIRPORTS.get(dest_code, {"iata": dest_code, "name": f"{dest_code}机场"})
            else:  # arrivals
                destination = AIRPORTS.get(airport_code, {"iata": airport_code, "name": f"{airport_code}机场"})
                airports_list = [a for a in AIRPORTS.keys() if a != airport_code]
                origin_code = random.choice(airports_list) if airports_list else "PEK"
                origin = AIRPORTS.get(origin_code, {"iata": origin_code, "name": f"{origin_code}机场"})
            
            # 生成时间
            now = datetime.now()
            time_offset = random.randint(-120, 240)  # -2小时到+4小时
            flight_time = now + timedelta(minutes=time_offset)
            
            # 状态
            if time_offset < -30:
                status = "到达" if flight_type == 'arrivals' else "起飞"
                delay = random.randint(0, 60) if random.random() < 0.3 else 0
            elif time_offset < 0:
                status = "到达中" if flight_type == 'arrivals' else "起飞"
                delay = random.randint(0, 45) if random.random() < 0.4 else 0
            elif time_offset < 60:
                status = "登机" if flight_type == 'departures' else "预计"
                delay = random.randint(0, 30) if random.random() < 0.2 else 0
            elif time_offset < 120:
                status = "值机" if flight_type == 'departures' else "预计"
                delay = 0
            else:
                status = "计划"
                delay = 0
            
            flight_data = {
                "flight_number": flight_num,
                "airline": AIRLINES.get(airline, {"name": "未知航空"}),
                "aircraft": random.choice(["B737", "A320", "A321", "B787"]),
                "origin": origin,
                "destination": destination,
                "scheduled_time": flight_time.strftime("%H:%M"),
                "estimated_time": (flight_time + timedelta(minutes=delay)).strftime("%H:%M"),
                "status": status,
                "delay_minutes": delay,
                "terminal": random.choice(["T1", "T2", "T3"]),
                "gate": f"{chr(65 + random.randint(0, 8))}{random.randint(1, 50)}",
                "baggage_claim": random.choice(["1", "2", "3", "4"]) if flight_type == 'arrivals' else None
            }
            
            flights.append(flight_data)
        
        # 按时间排序
        flights.sort(key=lambda x: x["scheduled_time"])
        
        return jsonify({
            "status": "success",
            "data": {
                "airport": AIRPORTS.get(airport_code, {"iata": airport_code}),
                "type": flight_type,
                "flights": flights[:limit],
                "stats": {
                    "total": len(flights),
                    "delayed": len([f for f in flights if f["delay_minutes"] > 15]),
                    "average_delay": sum(f["delay_minutes"] for f in flights) / max(len(flights), 1)
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/airline/<airline_code>/stats')
def get_airline_stats(airline_code):
    """获取航空公司统计"""
    try:
        # 模拟统计数据
        stats = {
            "airline": AIRLINES.get(airline_code, {"name": "未知航空"}),
            "performance": {
                "on_time_performance": round(random.uniform(0.70, 0.90), 3),
                "average_delay": random.randint(10, 30),
                "cancellation_rate": round(random.uniform(0.01, 0.05), 3),
                "completion_factor": round(random.uniform(0.95, 0.99), 3)
            },
            "fleet": {
                "total_aircraft": random.randint(50, 300),
                "average_age": round(random.uniform(5, 12), 1),
                "main_types": [
                    {"type": "B737", "count": random.randint(20, 100)},
                    {"type": "A320", "count": random.randint(15, 80)},
                    {"type": "A330", "count": random.randint(5, 30)},
                    {"type": "B787", "count": random.randint(3, 20)}
                ]
            },
            "routes": {
                "domestic": random.randint(50, 200),
                "international": random.randint(10, 50),
                "top_routes": [
                    {"route": "PEK-SHA", "flights_per_day": random.randint(10, 30)},
                    {"route": "CAN-PVG", "flights_per_day": random.randint(8, 25)},
                    {"route": "CTU-SZX", "flights_per_day": random.randint(5, 20)}
                ]
            },
            "reputation": {
                "punctuality_rank": random.randint(1, 20),
                "service_rating": round(random.uniform(3.5, 4.5), 1),
                "safety_rating": round(random.uniform(4.0, 5.0), 1)
            }
        }
        
        return jsonify({
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 启动模拟航班API服务器...")
    print("🌐 接口地址: http://localhost:8000")
    print("📡 可用接口:")
    print("  GET /api/v1/flight/<航班号>          - 航班实时信息")
    print("  GET /api/v1/flight/<航班号>/history - 航班历史数据")
    print("  GET /api/v1/flights/airport/<机场>  - 机场航班动态")
    print("  GET /api/v1/airline/<航司>/stats    - 航空公司统计")
    
    app.run(host='0.0.0.0', port=8000, debug=False)