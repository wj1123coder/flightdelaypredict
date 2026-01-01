#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据获取模块
获取航班状态、天气等实时数据
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import threading
from flask_socketio import emit

class RealTimeDataFetcher:
    """实时数据获取器"""
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        
        # 模拟的实时数据（实际项目应接入真实API）
        self.mock_flights = self._generate_mock_flights()
    
    def _generate_mock_flights(self):
        """生成模拟的实时航班数据"""
        airlines = ['CA', 'MU', 'CZ', 'HU', 'ZH', 'MF']
        airports = ['PEK', 'PVG', 'CAN', 'SZX', 'CTU', 'CKG', 'XIY', 'HGH', 'NKG', 'TAO']
        
        flights = []
        for i in range(20):
            airline = airlines[i % len(airlines)]
            origin = airports[i % len(airports)]
            destination = airports[(i + 3) % len(airports)]
            
            # 随机状态
            statuses = ['计划', '值机', '登机', '起飞', '到达', '延误', '取消']
            weights = [0.3, 0.15, 0.1, 0.15, 0.1, 0.15, 0.05]
            
            # 基于时间和航空公司调整权重
            hour = datetime.now().hour
            if 7 <= hour <= 9:
                weights = [0.1, 0.3, 0.2, 0.1, 0.1, 0.15, 0.05]  # 更多值机/登机
            elif 17 <= hour <= 19:
                weights = [0.2, 0.1, 0.1, 0.3, 0.1, 0.15, 0.05]  # 更多起飞
            
            import random
            status = random.choices(statuses, weights=weights)[0]
            
            # 模拟延误时间
            delay_minutes = random.randint(0, 120) if status == '延误' else 0
            
            flights.append({
                'flight_number': f"{airline}{random.randint(1000, 9999)}",
                'airline': airline,
                'origin': origin,
                'destination': destination,
                'status': status,
                'delay_minutes': delay_minutes,
                'gate': f"{chr(65 + (i % 8))}{random.randint(1, 50)}",
                'scheduled': f"{random.randint(6, 22)}:{random.randint(0, 59):02d}",
                'estimated': f"{random.randint(6, 22)}:{random.randint(0, 59):02d}",
                'actual': f"{random.randint(6, 22)}:{random.randint(0, 59):02d}" if status == '到达' else None,
                'last_updated': datetime.now().isoformat()
            })
        
        return flights
    
    def get_flight_status(self, flight_number):
        """获取航班实时状态"""
        cache_key = f"flight_{flight_number}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return data
        
        # 模拟API调用（实际项目应调用真实API）
        time.sleep(0.1)  # 模拟网络延迟
        
        # 在模拟数据中查找航班
        for flight in self.mock_flights:
            if flight['flight_number'] == flight_number:
                # 更新状态（模拟变化）
                import random
                statuses = ['计划', '值机', '登机', '起飞', '到达']
                current_idx = statuses.index(flight['status']) if flight['status'] in statuses else 0
                if current_idx < len(statuses) - 1 and random.random() < 0.3:
                    flight['status'] = statuses[current_idx + 1]
                
                # 缓存结果
                self.cache[cache_key] = (datetime.now(), flight)
                return flight
        
        # 如果没有找到，创建新的模拟航班
        airlines = ['CA', 'MU', 'CZ', 'HU', 'ZH', 'MF']
        airports = ['PEK', 'PVG', 'CAN', 'SZX', 'CTU']
        
        airline = flight_number[:2] if flight_number[:2] in airlines else airlines[0]
        status = '计划'  # 默认状态
        
        mock_flight = {
            'flight_number': flight_number,
            'airline': airline,
            'origin': airports[0],
            'destination': airports[1],
            'status': status,
            'delay_minutes': 0,
            'gate': f"Gate {random.randint(1, 50)}",
            'scheduled': '12:00',
            'estimated': '12:00',
            'actual': None,
            'last_updated': datetime.now().isoformat()
        }
        
        self.cache[cache_key] = (datetime.now(), mock_flight)
        return mock_flight
    
    def get_weather_data(self, airport_code):
        """获取机场天气数据"""
        cache_key = f"weather_{airport_code}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return data
        
        # 模拟天气数据（实际项目应调用天气API）
        import random
        
        # 根据季节和地区模拟天气
        month = datetime.now().month
        
        if month in [12, 1, 2]:  # 冬季
            conditions = ['晴', '多云', '阴', '雾', '小雪', '中雪']
            temperatures = range(-10, 10)
        elif month in [6, 7, 8]:  # 夏季
            conditions = ['晴', '多云', '雷阵雨', '小雨', '中雨', '大雨']
            temperatures = range(20, 35)
        else:  # 春秋季
            conditions = ['晴', '多云', '阴', '小雨']
            temperatures = range(10, 25)
        
        weather_data = {
            'airport': airport_code,
            'condition': random.choice(conditions),
            'temperature': random.choice(temperatures),
            'humidity': random.randint(40, 90),
            'wind_speed': random.randint(0, 20),
            'wind_direction': random.choice(['北', '东北', '东', '东南', '南', '西南', '西', '西北']),
            'visibility': random.choice(['良好', '一般', '较差']),
            'pressure': random.randint(980, 1030),
            'updated_at': datetime.now().isoformat()
        }
        
        # 缓存结果
        self.cache[cache_key] = (datetime.now(), weather_data)
        
        return weather_data
    
    def get_historical_delay_stats(self, airline=None, airport=None):
        """获取历史延误统计"""
        # 模拟历史统计数据（实际项目应从数据库获取）
        stats = {
            'overall': {
                'total_flights': 10000,
                'delayed_flights': 2500,
                'delay_rate': 0.25,
                'avg_delay_minutes': 28,
                'on_time_rate': 0.75
            },
            'by_airline': {
                'CA': {'delay_rate': 0.18, 'avg_delay': 22},
                'MU': {'delay_rate': 0.22, 'avg_delay': 26},
                'CZ': {'delay_rate': 0.20, 'avg_delay': 24},
                'HU': {'delay_rate': 0.25, 'avg_delay': 30},
                'ZH': {'delay_rate': 0.15, 'avg_delay': 18}
            },
            'by_airport': {
                'PEK': {'delay_rate': 0.25, 'avg_delay': 30},
                'PVG': {'delay_rate': 0.22, 'avg_delay': 26},
                'CAN': {'delay_rate': 0.20, 'avg_delay': 24},
                'SZX': {'delay_rate': 0.18, 'avg_delay': 22},
                'CTU': {'delay_rate': 0.15, 'avg_delay': 18}
            },
            'by_hour': {
                '06-08': {'delay_rate': 0.30, 'avg_delay': 35},
                '08-10': {'delay_rate': 0.35, 'avg_delay': 40},
                '10-12': {'delay_rate': 0.20, 'avg_delay': 25},
                '12-14': {'delay_rate': 0.18, 'avg_delay': 22},
                '14-16': {'delay_rate': 0.22, 'avg_delay': 26},
                '16-18': {'delay_rate': 0.28, 'avg_delay': 32},
                '18-20': {'delay_rate': 0.32, 'avg_delay': 38},
                '20-22': {'delay_rate': 0.15, 'avg_delay': 18},
                '22-24': {'delay_rate': 0.10, 'avg_delay': 12},
                '00-06': {'delay_rate': 0.08, 'avg_delay': 10}
            }
        }
        
        # 根据查询条件过滤
        result = {'overall': stats['overall']}
        
        if airline and airline in stats['by_airline']:
            result['airline'] = stats['by_airline'][airline]
        
        if airport:
            if airport in stats['by_airport']:
                result['airport'] = stats['by_airport'][airport]
            
            # 添加上下游机场影响
            result['related_airports'] = {}
            for code, data in stats['by_airport'].items():
                if code != airport:
                    result['related_airports'][code] = data
        
        # 添加时间分析
        hour = datetime.now().hour
        for time_range, data in stats['by_hour'].items():
            start, end = map(int, time_range.split('-'))
            if start <= hour < end:
                result['current_hour'] = data
                break
        
        return result
    
    def start_real_time_updates(self):
        """启动实时数据更新"""
        if not self.socketio:
            print("⚠️  SocketIO不可用，无法启动实时更新")
            return
        
        def update_loop():
            """实时更新循环"""
            while True:
                try:
                    # 更新航班状态
                    updated_flights = []
                    for flight in self.mock_flights[:10]:  # 只更新前10个航班
                        import random
                        if random.random() < 0.2:  # 20%概率更新
                            # 模拟状态变化
                            statuses = ['计划', '值机', '登机', '起飞', '到达']
                            if flight['status'] in statuses:
                                idx = statuses.index(flight['status'])
                                if idx < len(statuses) - 1:
                                    flight['status'] = statuses[idx + 1]
                            
                            # 更新时间和延误
                            flight['last_updated'] = datetime.now().isoformat()
                            if flight['status'] == '延误':
                                flight['delay_minutes'] = random.randint(5, 60)
                            
                            updated_flights.append(flight)
                    
                    if updated_flights:
                        # 发送实时更新
                        self.socketio.emit('flight_updates', {
                            'flights': updated_flights,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # 每10秒更新一次
                    time.sleep(10)
                    
                except Exception as e:
                    print(f"❌ 实时更新失败: {e}")
                    time.sleep(30)  # 出错后等待更长时间
        
        # 启动更新线程
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        print("✅ 实时数据更新已启动")
    
    def get_traffic_conditions(self, airport_code):
        """获取机场交通状况"""
        # 模拟交通状况
        import random
        
        hour = datetime.now().hour
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            congestion = random.choice(['拥堵', '缓慢', '繁忙'])
            waiting_time = random.randint(30, 90)
        elif 10 <= hour <= 16:
            congestion = random.choice(['畅通', '一般', '缓慢'])
            waiting_time = random.randint(15, 45)
        else:
            congestion = random.choice(['畅通', '非常畅通'])
            waiting_time = random.randint(5, 20)
        
        return {
            'airport': airport_code,
            'congestion_level': congestion,
            'estimated_waiting_time': waiting_time,
            'peak_hours': ['07:00-09:00', '17:00-19:00'],
            'recommended_arrival_time': f"提前{waiting_time + 30}分钟",
            'updated_at': datetime.now().isoformat()
        }

# 创建全局实例
data_fetcher = RealTimeDataFetcher()

if __name__ == '__main__':
    # 测试数据获取器
    print("🧪 测试实时数据获取器...")
    
    fetcher = RealTimeDataFetcher()
    
    # 测试航班状态查询
    flight_status = fetcher.get_flight_status('CA1234')
    print(f"\n📊 航班状态查询:")
    print(f"  航班号: {flight_status['flight_number']}")
    print(f"  状态: {flight_status['status']}")
    print(f"  延误: {flight_status['delay_minutes']}分钟")
    print(f"  登机口: {flight_status['gate']}")
    
    # 测试天气查询
    weather = fetcher.get_weather_data('PEK')
    print(f"\n🌤️ 天气查询:")
    print(f"  机场: {weather['airport']}")
    print(f"  天气: {weather['condition']}")
    print(f"  温度: {weather['temperature']}°C")
    print(f"  风速: {weather['wind_speed']} km/h")
    
    # 测试历史统计
    stats = fetcher.get_historical_delay_stats('CA', 'PEK')
    print(f"\n📈 历史统计:")
    print(f"  总体延误率: {stats['overall']['delay_rate']*100:.1f}%")
    if 'airline' in stats:
        print(f"  国航延误率: {stats['airline']['delay_rate']*100:.1f}%")
    if 'airport' in stats:
        print(f"  首都机场延误率: {stats['airport']['delay_rate']*100:.1f}%")
    
    # 测试交通状况
    traffic = fetcher.get_traffic_conditions('PEK')
    print(f"\n🚗 交通状况:")
    print(f"  拥堵程度: {traffic['congestion_level']}")
    print(f"  预计等待: {traffic['estimated_waiting_time']}分钟")
    print(f"  建议到达: {traffic['recommended_arrival_time']}")
    
    print("\n✅ 数据获取器测试完成")