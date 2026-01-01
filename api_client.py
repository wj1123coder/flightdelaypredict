#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端
用于连接航旅纵横/飞常准等真实API
当前使用模拟API
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import hmac
import base64

class FlightAPIClient:
    """航班API客户端"""
    
    def __init__(self, use_mock=True, api_key=None, api_secret=None):
        """
        初始化API客户端
        
        Args:
            use_mock: 是否使用模拟API
            api_key: 真实API密钥
            api_secret: 真实API密钥
        """
        self.use_mock = use_mock
        self.api_key = api_key
        self.api_secret = api_secret
        
        # API端点配置
        self.endpoints = {
            'mock_flight': 'http://localhost:8000/api/v1',
            'mock_weather': 'http://localhost:8001/api/v1',
            # 真实API端点（需要申请后填写）
            'real_flight': 'https://api.example.com/flight/v1',
            'real_weather': 'https://api.example.com/weather/v1'
        }
        
        # 请求头
        self.headers = {
            'User-Agent': 'FlightDelayPrediction/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if api_key:
            self.headers['X-API-Key'] = api_key
    
    def get_flight_info(self, flight_number: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取航班信息
        
        Args:
            flight_number: 航班号，如CA1234
            date: 日期，格式YYYY-MM-DD，默认为今天
            
        Returns:
            航班信息字典
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if self.use_mock:
            # 使用模拟API
            try:
                url = f"{self.endpoints['mock_flight']}/flight/{flight_number}"
                params = {'date': date}
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"❌ 模拟API请求失败: {e}")
                return self._generate_mock_flight_data(flight_number, date)
        else:
            # 使用真实API（需要申请后实现）
            return self._call_real_flight_api(flight_number, date)
    
    def get_flight_history(self, flight_number: str, days: int = 7) -> Dict[str, Any]:
        """
        获取航班历史数据
        
        Args:
            flight_number: 航班号
            days: 查询天数
            
        Returns:
            航班历史数据
        """
        if self.use_mock:
            try:
                url = f"{self.endpoints['mock_flight']}/flight/{flight_number}/history"
                params = {'days': days}
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"❌ 模拟历史数据请求失败: {e}")
                return self._generate_mock_history_data(flight_number, days)
        else:
            return self._call_real_history_api(flight_number, days)
    
    def get_airport_flights(self, airport_code: str, flight_type: str = 'departures', 
                           limit: int = 20) -> Dict[str, Any]:
        """
        获取机场航班动态
        
        Args:
            airport_code: 机场代码
            flight_type: 类型，departures/arrivals
            limit: 限制数量
            
        Returns:
            机场航班数据
        """
        if self.use_mock:
            try:
                url = f"{self.endpoints['mock_flight']}/flights/airport/{airport_code}"
                params = {'type': flight_type, 'limit': limit}
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"❌ 模拟机场数据请求失败: {e}")
                return self._generate_mock_airport_data(airport_code, flight_type, limit)
        else:
            return self._call_real_airport_api(airport_code, flight_type, limit)
    
    def get_airport_weather(self, airport_code: str) -> Dict[str, Any]:
        """
        获取机场天气
        
        Args:
            airport_code: 机场代码
            
        Returns:
            天气数据
        """
        if self.use_mock:
            try:
                url = f"{self.endpoints['mock_weather']}/weather/airport/{airport_code}"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"❌ 模拟天气数据请求失败: {e}")
                return self._generate_mock_weather_data(airport_code)
        else:
            return self._call_real_weather_api(airport_code)
    
    def get_weather_forecast(self, airport_code: str) -> Dict[str, Any]:
        """
        获取天气预报
        
        Args:
            airport_code: 机场代码
            
        Returns:
            天气预报数据
        """
        if self.use_mock:
            try:
                url = f"{self.endpoints['mock_weather']}/weather/forecast/{airport_code}"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"❌ 模拟天气预报请求失败: {e}")
                return self._generate_mock_forecast_data(airport_code)
        else:
            return self._call_real_forecast_api(airport_code)
    
    def get_airline_stats(self, airline_code: str) -> Dict[str, Any]:
        """
        获取航空公司统计
        
        Args:
            airline_code: 航空公司代码
            
        Returns:
            航空公司统计数据
        """
        if self.use_mock:
            try:
                url = f"{self.endpoints['mock_flight']}/airline/{airline_code}/stats"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
            except Exception as e:
                print(f"❌ 模拟航司统计请求失败: {e}")
                return self._generate_mock_airline_stats(airline_code)
        else:
            return self._call_real_airline_api(airline_code)
    
    # ========== 模拟数据生成方法 ==========
    
    def _generate_mock_flight_data(self, flight_number: str, date: str) -> Dict[str, Any]:
        """生成模拟航班数据"""
        # 简化的模拟数据生成
        import random
        
        airlines = {
            'CA': '中国国际航空', 'MU': '中国东方航空', 'CZ': '中国南方航空',
            'HU': '海南航空', 'ZH': '深圳航空', 'MF': '厦门航空'
        }
        
        airline_code = flight_number[:2]
        airline_name = airlines.get(airline_code, '未知航空')
        
        # 随机状态
        statuses = ['计划', '值机', '登机', '起飞', '到达', '延误']
        weights = [0.3, 0.2, 0.1, 0.15, 0.15, 0.1]
        status = random.choices(statuses, weights=weights)[0]
        
        delay = random.randint(0, 120) if status == '延误' else 0
        
        return {
            "status": "success",
            "data": {
                "flight": {
                    "number": flight_number,
                    "airline": {"name": airline_name, "iata": airline_code},
                    "aircraft": {"type": random.choice(["B737", "A320", "A330"])}
                },
                "departure": {
                    "airport": {"iata": "PEK", "name": "北京首都国际机场"},
                    "scheduled": f"{date} 08:30",
                    "estimated": f"{date} 08:{30 + delay}",
                    "gate": f"Gate {random.randint(1, 50)}"
                },
                "arrival": {
                    "airport": {"iata": "PVG", "name": "上海浦东国际机场"},
                    "scheduled": f"{date} 10:45",
                    "estimated": f"{date} 10:{45 + delay}"
                },
                "status": {
                    "text": status,
                    "delay": delay,
                    "updated": datetime.now().isoformat()
                }
            }
        }
    
    def _generate_mock_history_data(self, flight_number: str, days: int) -> Dict[str, Any]:
        """生成模拟历史数据"""
        import random
        from datetime import datetime, timedelta
        
        history = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 随机延误
            delay = random.randint(0, 120)
            if delay <= 15:
                status = "准点"
            elif delay <= 60:
                status = "延误"
            else:
                status = "严重延误"
            
            history.append({
                "date": date,
                "flight_number": flight_number,
                "delay_minutes": delay,
                "status": status,
                "load_factor": random.randint(60, 95)
            })
        
        return {
            "status": "success",
            "data": {
                "flight": flight_number,
                "history": history,
                "stats": {
                    "total_flights": days,
                    "on_time": len([h for h in history if h["delay_minutes"] <= 15]),
                    "avg_delay": sum(h["delay_minutes"] for h in history) / days
                }
            }
        }
    
    def _generate_mock_airport_data(self, airport_code: str, flight_type: str, limit: int) -> Dict[str, Any]:
        """生成模拟机场数据"""
        import random
        
        airports = {
            'PEK': '北京首都', 'PVG': '上海浦东', 'CAN': '广州白云',
            'SZX': '深圳宝安', 'CTU': '成都天府'
        }
        
        airport_name = airports.get(airport_code, f"{airport_code}机场")
        
        flights = []
        for i in range(limit):
            airlines = ['CA', 'MU', 'CZ', 'HU', 'ZH']
            airline = random.choice(airlines)
            
            if flight_type == 'departures':
                dest_codes = [c for c in airports.keys() if c != airport_code]
                dest = random.choice(dest_codes) if dest_codes else 'PVG'
                route = f"{airport_code}-{dest}"
            else:
                origin_codes = [c for c in airports.keys() if c != airport_code]
                origin = random.choice(origin_codes) if origin_codes else 'PEK'
                route = f"{origin}-{airport_code}"
            
            delay = random.randint(0, 90) if random.random() < 0.3 else 0
            
            flights.append({
                "flight_number": f"{airline}{random.randint(1000, 9999)}",
                "airline": {"name": "测试航空", "iata": airline},
                "route": route,
                "scheduled_time": f"{random.randint(6, 22):02d}:{random.randint(0, 59):02d}",
                "estimated_time": f"{random.randint(6, 22):02d}:{random.randint(0, 59):02d}",
                "status": "延误" if delay > 15 else "准点",
                "delay_minutes": delay,
                "gate": f"Gate {random.randint(1, 50)}"
            })
        
        return {
            "status": "success",
            "data": {
                "airport": {"iata": airport_code, "name": airport_name},
                "type": flight_type,
                "flights": flights
            }
        }
    
    def _generate_mock_weather_data(self, airport_code: str) -> Dict[str, Any]:
        """生成模拟天气数据"""
        import random
        
        conditions = ['晴', '多云', '小雨', '中雨', '大雨', '雾']
        condition = random.choice(conditions)
        
        if condition == '晴':
            impact = 0.0
        elif condition == '多云':
            impact = 0.05
        elif condition == '小雨':
            impact = 0.15
        elif condition == '中雨':
            impact = 0.30
        elif condition == '大雨':
            impact = 0.50
        else:  # 雾
            impact = 0.35
        
        return {
            "status": "success",
            "data": {
                "location": {"airport": airport_code, "city": "测试城市"},
                "current": {
                    "temperature": random.randint(10, 30),
                    "condition": condition,
                    "humidity": random.randint(40, 90),
                    "wind_speed": random.randint(0, 20),
                    "visibility": random.choice(["良好", "一般", "较差"])
                },
                "flight_impact": {
                    "delay_probability": impact,
                    "impact_level": "轻微影响" if impact < 0.3 else "中度影响",
                    "recommendation": "天气条件基本正常" if impact < 0.3 else "可能有延误"
                }
            }
        }
    
    def _generate_mock_forecast_data(self, airport_code: str) -> Dict[str, Any]:
        """生成模拟预报数据"""
        import random
        from datetime import datetime, timedelta
        
        forecast = []
        now = datetime.now()
        
        for i in range(3):  # 3天预报
            date = now + timedelta(days=i)
            
            conditions = ['晴', '多云', '小雨', '阴']
            condition = random.choice(conditions)
            
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                "max_temp": random.randint(15, 30),
                "min_temp": random.randint(5, 20),
                "condition": condition,
                "precipitation_probability": random.randint(0, 100) if "雨" in condition else random.randint(0, 30)
            })
        
        return {
            "status": "success",
            "data": {
                "location": {"airport": airport_code},
                "forecast": forecast
            }
        }
    
    def _generate_mock_airline_stats(self, airline_code: str) -> Dict[str, Any]:
        """生成模拟航空公司统计"""
        import random
        
        airlines = {
            'CA': '中国国际航空', 'MU': '中国东方航空', 'CZ': '中国南方航空',
            'HU': '海南航空', '9C': '春秋航空'
        }
        
        airline_name = airlines.get(airline_code, "测试航空")
        
        return {
            "status": "success",
            "data": {
                "airline": {"name": airline_name, "iata": airline_code},
                "performance": {
                    "on_time_performance": round(random.uniform(0.70, 0.90), 3),
                    "average_delay": random.randint(10, 30),
                    "cancellation_rate": round(random.uniform(0.01, 0.05), 3)
                },
                "fleet": {
                    "total_aircraft": random.randint(50, 300)
                }
            }
        }
    
    # ========== 真实API方法（需要申请后实现） ==========
    
    def _call_real_flight_api(self, flight_number: str, date: str) -> Dict[str, Any]:
        """调用真实航班API"""
        # 这里需要根据实际API文档实现
        # 以下是示例代码
        
        if not self.api_key:
            raise ValueError("需要API密钥才能调用真实API")
        
        # 构建请求URL
        url = f"{self.endpoints['real_flight']}/flight/{flight_number}"
        
        # 添加认证头
        headers = self.headers.copy()
        if self.api_secret:
            # 生成签名（根据API文档要求）
            timestamp = str(int(time.time()))
            signature = self._generate_signature(timestamp)
            headers['X-Timestamp'] = timestamp
            headers['X-Signature'] = signature
        
        # 发送请求
        params = {
            'date': date,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 真实API请求失败: {e}")
            # 失败时回退到模拟数据
            return self._generate_mock_flight_data(flight_number, date)
    
    def _generate_signature(self, timestamp: str) -> str:
        """生成API签名"""
        # 根据API文档要求实现签名算法
        # 通常是HMAC-SHA256
        
        message = f"{timestamp}{self.api_key}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _call_real_history_api(self, flight_number: str, days: int) -> Dict[str, Any]:
        """调用真实历史数据API"""
        # 实现类似_call_real_flight_api
        return self._generate_mock_history_data(flight_number, days)
    
    def _call_real_airport_api(self, airport_code: str, flight_type: str, limit: int) -> Dict[str, Any]:
        """调用真实机场数据API"""
        # 实现类似_call_real_flight_api
        return self._generate_mock_airport_data(airport_code, flight_type, limit)
    
    def _call_real_weather_api(self, airport_code: str) -> Dict[str, Any]:
        """调用真实天气API"""
        # 实现类似_call_real_flight_api
        return self._generate_mock_weather_data(airport_code)
    
    def _call_real_forecast_api(self, airport_code: str) -> Dict[str, Any]:
        """调用真实预报API"""
        # 实现类似_call_real_flight_api
        return self._generate_mock_forecast_data(airport_code)
    
    def _call_real_airline_api(self, airline_code: str) -> Dict[str, Any]:
        """调用真实航空公司API"""
        # 实现类似_call_real_flight_api
        return self._generate_mock_airline_stats(airline_code)

# 创建全局客户端实例
api_client = FlightAPIClient(use_mock=True)

if __name__ == '__main__':
    # 测试API客户端
    print("🧪 测试API客户端...")
    
    client = FlightAPIClient(use_mock=True)
    
    # 测试航班信息
    print("\n1. 测试航班信息查询:")
    result = client.get_flight_info('CA1234', '2024-01-15')
    if result['status'] == 'success':
        flight = result['data']['flight']
        status = result['data']['status']
        print(f"   航班: {flight['number']}")
        print(f"   航空公司: {flight['airline']['name']}")
        print(f"   状态: {status['text']}")
        print(f"   延误: {status['delay']}分钟")
    
    # 测试天气信息
    print("\n2. 测试天气信息查询:")
    result = client.get_airport_weather('PEK')
    if result['status'] == 'success':
        weather = result['data']['current']
        impact = result['data']['flight_impact']
        print(f"   天气: {weather['condition']}")
        print(f"   温度: {weather['temperature']}°C")
        print(f"   延误概率: {impact['delay_probability']*100:.1f}%")
        print(f"   影响等级: {impact['impact_level']}")
    
    # 测试机场动态
    print("\n3. 测试机场动态查询:")
    result = client.get_airport_flights('PEK', 'departures', 3)
    if result['status'] == 'success':
        flights = result['data']['flights']
        print(f"   获取到 {len(flights)} 个航班:")
        for flight in flights[:3]:
            print(f"   {flight['flight_number']}: {flight['route']} - {flight['status']}")
    
    print("\n✅ API客户端测试完成")