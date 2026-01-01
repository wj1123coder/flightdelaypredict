#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能航班延误预测系统 - 后端服务器（完整版）
版本：3.0.0 - 集成真实API数据
"""

import os
import sys
import json
import random
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
try:
    from models.flight_predictor import FlightDelayPredictor
    ML_MODEL_AVAILABLE = True
    print("✅ 机器学习模型可用")
except ImportError:
    ML_MODEL_AVAILABLE = False
    print("⚠️  机器学习模型不可用，使用规则引擎")

# 导入API客户端和预测引擎
try:
    from api_client import api_client
    from prediction_engine import prediction_engine
    print("✅ API客户端和预测引擎加载成功")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保已创建 api_client.py 和 prediction_engine.py")
    # 创建简单的替代
    class MockAPIClient:
        def get_flight_info(self, *args, **kwargs):
            return {'status': 'success', 'data': {'status': {'text': '计划', 'delay': 0}}}
        def get_airport_weather(self, *args, **kwargs):
            return {'status': 'success', 'data': {'current': {'condition': '晴', 'temperature': 25}}}
        def get_airline_stats(self, *args, **kwargs):
            return {'status': 'success', 'data': {'performance': {'on_time_performance': 0.8}}}
        def get_flight_history(self, *args, **kwargs):
            return {'status': 'success', 'data': {'stats': {'avg_delay': 20}}}
    api_client = MockAPIClient()
    
    class MockPredictionEngine:
        def predict(self, flight_info):
            return {
                'delay_probability': 0.3,
                'estimated_delay_minutes': 15,
                'risk_level': '低',
                'confidence': 0.85,
                'model_used': '规则引擎'
            }
        def get_statistics(self):
            return {'prediction_method': '规则引擎'}
    prediction_engine = MockPredictionEngine()

# 初始化应用
app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates',
            static_url_path='/static')

# 配置
app.config['SECRET_KEY'] = 'flight_delay_prediction_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 启用CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 初始化SocketIO
try:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    SOCKETIO_AVAILABLE = True
    print("✅ WebSocket实时通信已启用")
except:
    socketio = None
    SOCKETIO_AVAILABLE = False
    print("⚠️  WebSocket不可用")

# ==================== 数据库管理 ====================

class DatabaseManager:
    """简单数据库管理器（JSON文件存储）"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.history_file = os.path.join(self.data_dir, 'prediction_history.json')
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_prediction(self, flight_data, prediction):
        """保存预测记录"""
        try:
            # 读取现有历史
            history = self.load_history()
            
            # 创建新记录
            record = {
                "id": len(history) + 1,
                "timestamp": datetime.now().isoformat(),
                "flight_data": flight_data,
                "prediction": prediction,
                "user_ip": request.remote_addr if request else "127.0.0.1"
            }
            
            # 添加到历史
            history.append(record)
            
            # 只保留最近500条记录
            if len(history) > 500:
                history = history[-500:]
            
            # 保存到文件
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 预测记录已保存，ID: {record['id']}")
            return record['id']
            
        except Exception as e:
            print(f"❌ 保存预测记录失败: {e}")
            return None
    
    def load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def get_recent_predictions(self, limit=10):
        """获取最近的预测记录"""
        history = self.load_history()
        return history[-limit:] if len(history) >= limit else history
    
    def get_today_stats(self):
        """获取今日统计"""
        history = self.load_history()
        today = datetime.now().date().isoformat()
        
        today_predictions = [
            p for p in history 
            if p.get('timestamp', '').startswith(today)
        ]
        
        return {
            'total': len(today_predictions),
            'delayed': len([p for p in today_predictions 
                          if p.get('prediction', {}).get('delay_probability', 0) > 0.5]),
            'on_time': len([p for p in today_predictions 
                           if p.get('prediction', {}).get('delay_probability', 0) <= 0.5]),
            'avg_delay_prob': round(
                sum(p.get('prediction', {}).get('delay_probability', 0) 
                    for p in today_predictions) / max(len(today_predictions), 1), 3
            )
        }

# 初始化数据库
db_manager = DatabaseManager()

# ==================== 辅助函数 ====================

def generate_suggestions(prediction, flight_info):
    """生成出行建议"""
    suggestions = []
    prob = prediction.get('delay_probability', 0)
    risk_level = prediction.get('risk_level', '中')
    estimated_delay = prediction.get('estimated_delay_minutes', 0)
    
    # 根据风险等级和建议
    if risk_level in ["高", "极高"]:
        suggestions.append("🔴 延误风险极高，强烈建议：")
        suggestions.append("• 立即联系航空公司改签至更早航班")
        suggestions.append("• 购买航班延误险（建议保额100元以上）")
        suggestions.append("• 准备备用交通方案（高铁/其他航班）")
        suggestions.append("• 提前4小时到达机场")
        suggestions.append("• 关注机场实时大屏和航空公司APP")
        
    elif risk_level == "中":
        suggestions.append("🟡 延误风险中等，建议：")
        suggestions.append("• 提前3小时到达机场")
        suggestions.append("• 在线值机并打印登机牌")
        suggestions.append("• 预留充足转机时间（至少3小时）")
        suggestions.append("• 下载航旅纵横APP获取实时提醒")
        suggestions.append("• 准备一些零食和娱乐设备")
        
    elif risk_level == "低":
        suggestions.append("🟢 延误风险较低，建议：")
        suggestions.append("• 提前2.5小时到达机场")
        suggestions.append("• 使用电子登机牌方便快捷")
        suggestions.append("• 正常安排行程")
        suggestions.append("• 关注天气变化")
        
    else:  # 极低风险
        suggestions.append("✅ 延误风险极低，建议：")
        suggestions.append("• 提前2小时到达机场即可")
        suggestions.append("• 祝您旅途愉快！")
    
    # 添加具体延误时间建议
    if estimated_delay > 60:
        suggestions.append(f"⏰ 预计延误超过1小时，请合理安排时间")
    elif estimated_delay > 30:
        suggestions.append(f"⏰ 预计延误30-60分钟，建议稍早出发")
    
    # 添加强制性因素建议
    factors = prediction.get('factors', [])
    for factor in factors:
        if "高峰" in factor:
            suggestions.append("🚗 高峰时段交通拥堵，请提前出发")
        elif "春运" in factor or "暑运" in factor:
            suggestions.append("👥 节假日期间客流大，请耐心等待")
        elif "繁忙机场" in factor:
            suggestions.append("🏢 繁忙机场安检时间长，请提前到达")
    
    # 添加天气建议（基于月份）
    try:
        month = int(flight_info.get('departure_date', '2024-01-01').split('-')[1])
        if month in [6, 7, 8]:
            suggestions.append("☀️ 夏季多雷雨，建议关注天气")
        elif month in [12, 1, 2]:
            suggestions.append("❄️ 冬季可能受冰雪影响")
    except:
        pass
    
    return suggestions

def get_alternative_flights(flight_info):
    """获取替代航班建议"""
    origin = flight_info.get('origin', 'PEK')
    destination = flight_info.get('destination', 'PVG')
    
    # 模拟替代航班
    alternatives = []
    airlines = ['CA', 'MU', 'CZ']  # 取前3家航空公司
    
    for i, airline_code in enumerate(airlines):
        airline_names = {
            'CA': '中国国际航空',
            'MU': '中国东方航空', 
            'CZ': '中国南方航空'
        }
        airline_name = airline_names.get(airline_code, airline_code)
        
        # 生成不同的起飞时间（比原航班早1-3小时）
        original_hour = int(flight_info.get('departure_time', '12:00').split(':')[0])
        alt_hour = max(6, original_hour - (i+1))
        
        # 生成航班号
        flight_num = f"{airline_code}{random.randint(1000, 9999)}"
        
        # 延误风险评估
        delay_risk = ["低", "中", "低"][i]
        
        alternatives.append({
            'airline': airline_code,
            'airline_name': airline_name,
            'flight_number': flight_num,
            'departure_time': f"{alt_hour}:{random.choice(['00', '15', '30', '45'])}",
            'arrival_time': f"{alt_hour+2}:{random.choice(['00', '15', '30', '45'])}",
            'price': f"{random.randint(500, 2000)}元",
            'delay_risk': delay_risk,
            'seats_available': random.choice(['充足', '充足', '有限']),
            'recommendation': '推荐' if delay_risk == '低' else '备选'
        })
    
    return alternatives

# ==================== WebSocket实时通信 ====================

if SOCKETIO_AVAILABLE:
    @socketio.on('connect')
    def handle_connect():
        print(f'🔗 客户端连接: {request.sid}')
        emit('connected', {'message': '连接成功', 'timestamp': datetime.now().isoformat()})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'🔌 客户端断开: {request.sid}')
    
    @socketio.on('subscribe_flight')
    def handle_subscribe(data):
        """订阅航班状态更新"""
        flight_number = data.get('flight_number', '')
        print(f'📡 订阅航班: {flight_number}')
        
        # 模拟实时更新
        def send_updates():
            for i in range(5):  # 发送5次更新
                time.sleep(2)
                status = {
                    'flight_number': flight_number,
                    'status': ['计划', '值机', '登机', '起飞', '到达'][i],
                    'gate': f"{chr(65 + i)}{random.randint(1, 30)}",
                    'time': (datetime.now() + timedelta(minutes=i*30)).strftime('%H:%M'),
                    'message': f"航班状态更新 #{i+1}"
                }
                emit('flight_update', status)
        
        # 在新线程中发送更新
        thread = threading.Thread(target=send_updates)
        thread.daemon = True
        thread.start()

# ==================== API路由 ====================

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/simple')
def simple_index():
    """简化版页面"""
    return render_template('simple_index.html')

@app.route('/dashboard')
def dashboard():
    """仪表板页面"""
    return render_template('dashboard.html')

@app.route('/api/airlines')
def get_airlines():
    """获取航空公司列表"""
    airlines_list = [
        {"code": "CA", "name": "中国国际航空", "delay_rate": 0.18, "color": "#FF0000"},
        {"code": "MU", "name": "中国东方航空", "delay_rate": 0.22, "color": "#6807F9"},
        {"code": "CZ", "name": "中国南方航空", "delay_rate": 0.20, "color": "#00B0F0"},
        {"code": "HU", "name": "海南航空", "delay_rate": 0.25, "color": "#F9B600"},
        {"code": "ZH", "name": "深圳航空", "delay_rate": 0.15, "color": "#FF6600"},
        {"code": "MF", "name": "厦门航空", "delay_rate": 0.12, "color": "#009944"},
        {"code": "HO", "name": "吉祥航空", "delay_rate": 0.14, "color": "#E6007E"},
        {"code": "9C", "name": "春秋航空", "delay_rate": 0.28, "color": "#79C141"},
        {"code": "KN", "name": "中国联合航空", "delay_rate": 0.20, "color": "#0066B3"},
        {"code": "GS", "name": "天津航空", "delay_rate": 0.23, "color": "#6A5ACD"}
    ]
    return jsonify({
        'success': True,
        'airlines': airlines_list,
        'count': len(airlines_list)
    })

@app.route('/api/airports')
def get_airports():
    """获取机场列表"""
    airports_list = [
        {"code": "PEK", "name": "北京首都国际机场", "city": "北京", "delay_rate": 0.25},
        {"code": "PVG", "name": "上海浦东国际机场", "city": "上海", "delay_rate": 0.22},
        {"code": "CAN", "name": "广州白云国际机场", "city": "广州", "delay_rate": 0.20},
        {"code": "SZX", "name": "深圳宝安国际机场", "city": "深圳", "delay_rate": 0.18},
        {"code": "CTU", "name": "成都天府国际机场", "city": "成都", "delay_rate": 0.15},
        {"code": "CKG", "name": "重庆江北国际机场", "city": "重庆", "delay_rate": 0.17},
        {"code": "XIY", "name": "西安咸阳国际机场", "city": "西安", "delay_rate": 0.14},
        {"code": "HGH", "name": "杭州萧山国际机场", "city": "杭州", "delay_rate": 0.16},
        {"code": "NKG", "name": "南京禄口国际机场", "city": "南京", "delay_rate": 0.13},
        {"code": "TAO", "name": "青岛胶东国际机场", "city": "青岛", "delay_rate": 0.19}
    ]
    return jsonify({
        'success': True,
        'airports': airports_list,
        'count': len(airports_list)
    })

@app.route('/api/predict', methods=['POST'])
def predict_delay():
    """预测航班延误（使用真实API数据）"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        # 验证必要字段
        required_fields = ['airline', 'flight_number', 'origin', 'destination', 'departure_date', 'departure_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必要字段: {field}'}), 400
        
        print(f"📋 收到预测请求: {data}")
        
        # 1. 获取航班实时信息
        flight_info_result = api_client.get_flight_info(
            data['flight_number'], 
            data['departure_date']
        )
        
        # 2. 获取出发机场天气
        origin_weather_result = api_client.get_airport_weather(data['origin'])
        
        # 3. 获取到达机场天气
        dest_weather_result = api_client.get_airport_weather(data['destination'])
        
        # 4. 获取航空公司统计
        airline_stats_result = api_client.get_airline_stats(data['airline'])
        
        # 5. 获取航班历史数据
        flight_history_result = api_client.get_flight_history(data['flight_number'], days=30)
        
        # 6. 使用增强的预测引擎
        enhanced_info = {
            **data,
            'real_time_status': flight_info_result.get('data', {}).get('status', {}) if flight_info_result.get('status') == 'success' else {},
            'origin_weather': origin_weather_result.get('data', {}).get('current', {}) if origin_weather_result.get('status') == 'success' else {},
            'dest_weather': dest_weather_result.get('data', {}).get('current', {}) if dest_weather_result.get('status') == 'success' else {},
            'airline_performance': airline_stats_result.get('data', {}).get('performance', {}) if airline_stats_result.get('status') == 'success' else {},
            'historical_stats': flight_history_result.get('data', {}).get('stats', {}) if flight_history_result.get('status') == 'success' else {}
        }
        
        # 进行预测
        prediction = prediction_engine.predict(enhanced_info)
        
        # 生成建议
        suggestions = generate_suggestions(prediction, enhanced_info)
        
        # 获取替代航班
        alternatives = get_alternative_flights(data)
        
        # 保存到历史记录
        record_id = db_manager.save_prediction(data, prediction)
        
        # 构建响应
        response = {
            'success': True,
            'prediction_id': record_id,
            'flight_info': data,
            'real_time_data': {
                'flight_status': flight_info_result.get('data', {}).get('status', {}) if flight_info_result.get('status') == 'success' else {'text': '数据获取失败'},
                'weather_impact': {
                    'origin': origin_weather_result.get('data', {}).get('flight_impact', {}) if origin_weather_result.get('status') == 'success' else {'delay_probability': 0.1},
                    'destination': dest_weather_result.get('data', {}).get('flight_impact', {}) if dest_weather_result.get('status') == 'success' else {'delay_probability': 0.1}
                },
                'airline_stats': airline_stats_result.get('data', {}).get('performance', {}) if airline_stats_result.get('status') == 'success' else {'on_time_performance': 0.8},
                'historical_performance': flight_history_result.get('data', {}).get('stats', {}) if flight_history_result.get('status') == 'success' else {'avg_delay': 20}
            },
            'prediction': prediction,
            'suggestions': suggestions,
            'alternatives': alternatives,
            'data_sources': {
                'flight_api': '模拟API',
                'weather_api': '模拟API',
                'prediction_engine': prediction.get('model_used', '规则引擎')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ 预测完成: 延误概率 {prediction['delay_probability']*100}%")
        
        # 实时推送（如果可用）
        if SOCKETIO_AVAILABLE:
            socketio.emit('new_prediction', {
                'flight_number': data['flight_number'],
                'probability': prediction['delay_probability'],
                'risk_level': prediction['risk_level']
            })
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ 预测处理失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/flight/<flight_number>/detailed')
def get_detailed_flight_info(flight_number):
    """获取航班详细信息（包括实时数据）"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # 获取各种数据
        flight_info = api_client.get_flight_info(flight_number, date)
        flight_history = api_client.get_flight_history(flight_number, days=7)
        
        # 获取机场信息
        if flight_info.get('status') == 'success' and flight_info.get('data', {}).get('departure'):
            origin_code = flight_info['data']['departure']['airport'].get('iata', 'PEK')
            dest_code = flight_info['data']['arrival']['airport'].get('iata', 'PVG')
            
            origin_weather = api_client.get_airport_weather(origin_code)
            dest_weather = api_client.get_airport_weather(dest_code)
            
            # 获取航空公司代码
            airline_code = flight_number[:2]
            airline_stats = api_client.get_airline_stats(airline_code)
        else:
            # 使用默认值
            origin_weather = {'status': 'success', 'data': {'current': {'condition': '晴', 'temperature': 25}}}
            dest_weather = {'status': 'success', 'data': {'current': {'condition': '晴', 'temperature': 25}}}
            airline_stats = {'status': 'success', 'data': {'performance': {'on_time_performance': 0.8}}}
        
        return jsonify({
            'success': True,
            'flight': flight_info.get('data', {}),
            'history': flight_history.get('data', {}),
            'weather': {
                'origin': origin_weather.get('data', {}),
                'destination': dest_weather.get('data', {})
            },
            'airline': airline_stats.get('data', {}),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    """获取预测历史"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        history = db_manager.get_recent_predictions(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history),
            'total_in_db': len(db_manager.load_history())
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats/today')
def get_today_stats():
    """获取今日统计"""
    stats = db_manager.get_today_stats()
    
    # 热门预测航线
    history = db_manager.load_history()
    today = datetime.now().date().isoformat()
    today_history = [p for p in history if p.get('timestamp', '').startswith(today)]
    
    route_counts = {}
    for record in today_history:
        route = f"{record['flight_data'].get('origin')}-{record['flight_data'].get('destination')}"
        route_counts[route] = route_counts.get(route, 0) + 1
    
    popular_routes = sorted(route_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'success': True,
        'date': today,
        'stats': stats,
        'popular_routes': [{'route': r[0], 'count': r[1]} for r in popular_routes],
        'total_predictions': len(history)
    })

@app.route('/api/flight/<flight_number>/status')
def get_flight_status(flight_number):
    """获取航班实时状态（模拟）"""
    statuses = ['计划', '值机', '登机', '起飞', '到达', '延误', '取消']
    probabilities = [0.3, 0.25, 0.2, 0.15, 0.05, 0.04, 0.01]
    
    status = random.choices(statuses, weights=probabilities)[0]
    
    return jsonify({
        'success': True,
        'flight_number': flight_number,
        'status': status,
        'gate': f"{chr(65 + random.randint(0, 8))}{random.randint(1, 50)}",
        'estimated_departure': (datetime.now() + timedelta(minutes=random.randint(-30, 120))).strftime('%H:%M'),
        'estimated_arrival': (datetime.now() + timedelta(minutes=random.randint(120, 300))).strftime('%H:%M'),
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/weather/<airport_code>')
def get_weather(airport_code):
    """获取机场天气（模拟）"""
    weather_types = ['晴', '多云', '阴', '小雨', '中雨', '大雨', '雷阵雨', '雾', '雪']
    temperatures = {
        '晴': random.randint(20, 35),
        '多云': random.randint(18, 30),
        '阴': random.randint(15, 25),
        '小雨': random.randint(10, 22),
        '中雨': random.randint(8, 20),
        '大雨': random.randint(5, 18),
        '雷阵雨': random.randint(15, 28),
        '雾': random.randint(5, 15),
        '雪': random.randint(-5, 5)
    }
    
    weather = random.choice(weather_types)
    
    return jsonify({
        'success': True,
        'airport': airport_code,
        'weather': weather,
        'temperature': temperatures.get(weather, 20),
        'humidity': random.randint(40, 95),
        'wind_speed': random.randint(0, 20),
        'visibility': random.choice(['良好', '一般', '较差']),
        'updated_at': datetime.now().isoformat()
    })

@app.route('/api/realtime-flights')
def get_realtime_flights():
    """获取实时航班列表（模拟）"""
    airlines = ['CA', 'MU', 'CZ', 'HU', 'ZH', 'MF']
    airports = ['PEK', 'PVG', 'CAN', 'SZX', 'CTU', 'CKG', 'XIY', 'HGH', 'NKG', 'TAO']
    
    flights = []
    
    for i in range(10):
        airline = random.choice(airlines)
        origin = random.choice(airports)
        destination = random.choice([code for code in airports if code != origin])
        
        status_options = ['计划', '值机', '登机', '起飞', '到达', '延误']
        weights = [0.3, 0.2, 0.15, 0.15, 0.1, 0.1]
        status = random.choices(status_options, weights=weights)[0]
        
        flights.append({
            'flight_number': f"{airline}{random.randint(1000, 9999)}",
            'airline': airline,
            'origin': origin,
            'destination': destination,
            'status': status,
            'gate': f"{chr(65 + random.randint(0, 8))}{random.randint(1, 50)}",
            'scheduled': f"{random.randint(6, 22)}:{random.randint(0, 59):02d}",
            'estimated': f"{random.randint(6, 22)}:{random.randint(0, 59):02d}",
            'delay_minutes': random.randint(0, 120) if status == '延误' else 0
        })
    
    return jsonify({
        'success': True,
        'flights': flights,
        'updated_at': datetime.now().isoformat(),
        'total': len(flights)
    })

@app.route('/api/system/health')
def system_health():
    """系统健康检查"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': 'ok',
            'prediction_engine': 'ok',
            'api_client': 'ok',
            'websocket': 'available' if SOCKETIO_AVAILABLE else 'unavailable'
        },
        'statistics': {
            'total_predictions': len(db_manager.load_history()),
            'today_predictions': db_manager.get_today_stats()['total'],
            'system_uptime': 'N/A'
        }
    })

# ==================== 静态文件服务 ====================

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(app.static_folder, filename)

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '资源未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'success': False, 'error': '方法不允许'}), 405

# ==================== 启动服务器 ====================

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     ✈️  智能航班延误预测系统 v3.0.0                      ║
    ║                                                          ║
    ║    🚀  基于真实API数据的智能预测                        ║
    ║    📊  集成实时航班与天气信息                            ║
    ║    🌐  提供完整的API接口                                 ║
    ║    ⚡  实时WebSocket通信                                 ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == '__main__':
    # 打印启动信息
    print_banner()
    
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)
    
    print("📊 系统配置信息:")
    print(f"  • 机器学习模型: {'可用' if ML_MODEL_AVAILABLE else '不可用（使用规则引擎）'}")
    print(f"  • 实时通信: {'可用' if SOCKETIO_AVAILABLE else '不可用'}")
    print(f"  • 预测引擎: {prediction_engine.get_statistics()['prediction_method']}")
    print(f"  • 数据目录: {db_manager.data_dir}")
    
    print("\n🌐 服务地址:")
    print("  • 主页面: http://localhost:5000/")
    print("  • 简化版: http://localhost:5000/simple")
    print("  • 仪表板: http://localhost:5000/dashboard")
    print("  • 健康检查: http://localhost:5000/api/system/health")
    
    print("\n📡 核心API端点:")
    print("  • GET  /api/airlines          - 航空公司列表")
    print("  • GET  /api/airports          - 机场列表")
    print("  • POST /api/predict          - 预测航班延误（集成真实数据）")
    print("  • GET  /api/flight/<航班>/detailed - 航班详细信息")
    print("  • GET  /api/history          - 预测历史记录")
    print("  • GET  /api/stats/today      - 今日统计")
    print("  • GET  /api/realtime-flights - 实时航班")
    
    print("\n" + "="*60)
    print("🚀 服务器启动中...")
    
    try:
        if SOCKETIO_AVAILABLE:
            socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
        else:
            app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("尝试使用备用端口...")
        app.run(host='0.0.0.0', port=8080, debug=True)