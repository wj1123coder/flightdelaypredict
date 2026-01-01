#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能航班延误预测引擎
结合规则引擎和机器学习模型
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import os
import json

class DelayPredictionEngine:
    """航班延误预测引擎"""
    
    def __init__(self, use_ml=True):
        """
        初始化预测引擎
        
        Args:
            use_ml: 是否使用机器学习模型
        """
        self.use_ml = use_ml
        self.ml_model = None
        self.feature_encoder = None
        
        # 加载航空公司延误率数据（基于历史统计）
        self.airline_delay_stats = self._load_airline_stats()
        
        # 加载机场延误率数据
        self.airport_delay_stats = self._load_airport_stats()
        
        # 尝试加载机器学习模型
        if use_ml:
            self._load_ml_model()
    
    def _load_airline_stats(self):
        """加载航空公司延误统计数据"""
        # 基于真实数据的统计（可后期更新）
        return {
            'CA': {'name': '中国国际航空', 'delay_rate': 0.18, 'on_time_rate': 0.82},
            'MU': {'name': '中国东方航空', 'delay_rate': 0.22, 'on_time_rate': 0.78},
            'CZ': {'name': '中国南方航空', 'delay_rate': 0.20, 'on_time_rate': 0.80},
            'HU': {'name': '海南航空', 'delay_rate': 0.25, 'on_time_rate': 0.75},
            'ZH': {'name': '深圳航空', 'delay_rate': 0.15, 'on_time_rate': 0.85},
            'MF': {'name': '厦门航空', 'delay_rate': 0.12, 'on_time_rate': 0.88},
            'HO': {'name': '吉祥航空', 'delay_rate': 0.14, 'on_time_rate': 0.86},
            '9C': {'name': '春秋航空', 'delay_rate': 0.28, 'on_time_rate': 0.72},
            'KN': {'name': '中国联合航空', 'delay_rate': 0.20, 'on_time_rate': 0.80},
            'GS': {'name': '天津航空', 'delay_rate': 0.23, 'on_time_rate': 0.77}
        }
    
    def _load_airport_stats(self):
        """加载机场延误统计数据"""
        return {
            'PEK': {'name': '北京首都', 'delay_rate': 0.25, 'city': '北京'},
            'PVG': {'name': '上海浦东', 'delay_rate': 0.22, 'city': '上海'},
            'CAN': {'name': '广州白云', 'delay_rate': 0.20, 'city': '广州'},
            'SZX': {'name': '深圳宝安', 'delay_rate': 0.18, 'city': '深圳'},
            'CTU': {'name': '成都天府', 'delay_rate': 0.15, 'city': '成都'},
            'CKG': {'name': '重庆江北', 'delay_rate': 0.17, 'city': '重庆'},
            'XIY': {'name': '西安咸阳', 'delay_rate': 0.14, 'city': '西安'},
            'HGH': {'name': '杭州萧山', 'delay_rate': 0.16, 'city': '杭州'},
            'NKG': {'name': '南京禄口', 'delay_rate': 0.13, 'city': '南京'},
            'TAO': {'name': '青岛胶东', 'delay_rate': 0.19, 'city': '青岛'}
        }
    
    def _load_ml_model(self):
        """尝试加载机器学习模型"""
        model_path = os.path.join('models', 'flight_delay_model.pkl')
        encoder_path = os.path.join('models', 'feature_encoder.pkl')
        
        try:
            if os.path.exists(model_path) and os.path.exists(encoder_path):
                self.ml_model = joblib.load(model_path)
                self.feature_encoder = joblib.load(encoder_path)
                print("✅ 机器学习模型加载成功")
                return True
            else:
                print("⚠️  未找到机器学习模型文件，使用规则引擎")
                return False
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
            return False
    
    def predict(self, flight_info):
        """
        预测航班延误
        
        Args:
            flight_info: 航班信息字典，包含：
                - airline: 航空公司代码
                - flight_number: 航班号
                - origin: 出发机场代码
                - destination: 到达机场代码
                - departure_date: 出发日期 (YYYY-MM-DD)
                - departure_time: 出发时间 (HH:MM)
                
        Returns:
            预测结果字典
        """
        print(f"📊 预测航班: {flight_info}")
        
        try:
            # 使用机器学习模型（如果可用）
            if self.use_ml and self.ml_model:
                ml_result = self._predict_with_ml(flight_info)
                if ml_result:
                    return ml_result
            
            # 使用规则引擎
            return self._predict_with_rules(flight_info)
            
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            return self._get_default_prediction()
    
    def _predict_with_ml(self, flight_info):
        """使用机器学习模型预测"""
        try:
            # 准备特征
            features = self._prepare_features(flight_info)
            
            # 使用模型预测
            delay_prob = self.ml_model.predict_proba([features])[0][1]
            
            # 获取特征重要性（如果有的话）
            importance = None
            if hasattr(self.ml_model, 'feature_importances_'):
                importance = dict(zip(
                    self.feature_encoder.feature_names_in_,
                    self.ml_model.feature_importances_
                ))
            
            return self._format_prediction_result(
                delay_prob, 
                flight_info, 
                model_type="机器学习",
                importance=importance
            )
            
        except Exception as e:
            print(f"❌ 机器学习预测失败: {e}")
            return None
    
    def _predict_with_rules(self, flight_info):
        """使用规则引擎预测"""
        try:
            # 解析航班信息
            airline = flight_info.get('airline', 'CA')
            origin = flight_info.get('origin', 'PEK')
            destination = flight_info.get('destination', 'PVG')
            departure_date = flight_info.get('departure_date', '2024-01-01')
            departure_time = flight_info.get('departure_time', '12:00')
            
            # 解析日期时间
            datetime_str = f"{departure_date} {departure_time}"
            departure_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            
            hour = departure_datetime.hour
            month = departure_datetime.month
            weekday = departure_datetime.weekday()  # 0=周一
            day = departure_datetime.day
            
            # 基础延误概率
            base_prob = 0.15
            
            # 1. 航空公司因素 (权重: 30%)
            airline_factor = self._get_airline_factor(airline)
            base_prob += airline_factor * 0.3
            
            # 2. 机场因素 (权重: 25%)
            airport_factor = self._get_airport_factor(origin, destination)
            base_prob += airport_factor * 0.25
            
            # 3. 时间因素 (权重: 20%)
            time_factor = self._get_time_factor(hour, weekday)
            base_prob += time_factor * 0.2
            
            # 4. 季节因素 (权重: 15%)
            season_factor = self._get_season_factor(month, day)
            base_prob += season_factor * 0.15
            
            # 5. 航线因素 (权重: 10%)
            route_factor = self._get_route_factor(origin, destination)
            base_prob += route_factor * 0.10
            
            # 确保概率在合理范围内
            delay_prob = max(0.05, min(0.95, base_prob))
            
            # 分析影响因素
            factors = self._analyze_delay_factors(
                airline, origin, destination, hour, weekday, month, day
            )
            
            return self._format_prediction_result(
                delay_prob, 
                flight_info, 
                model_type="规则引擎",
                factors=factors
            )
            
        except Exception as e:
            print(f"❌ 规则引擎预测失败: {e}")
            return self._get_default_prediction()
    
    def _get_airline_factor(self, airline_code):
        """获取航空公司延误因子"""
        stats = self.airline_delay_stats.get(airline_code, {})
        return stats.get('delay_rate', 0.2)
    
    def _get_airport_factor(self, origin, destination):
        """获取机场延误因子"""
        origin_stats = self.airport_delay_stats.get(origin, {})
        dest_stats = self.airport_delay_stats.get(destination, {})
        
        origin_delay = origin_stats.get('delay_rate', 0.2)
        dest_delay = dest_stats.get('delay_rate', 0.2)
        
        # 出发和到达机场的平均延误率
        return (origin_delay + dest_delay) / 2
    
    def _get_time_factor(self, hour, weekday):
        """获取时间因子"""
        factor = 0
        
        # 高峰时段
        if 7 <= hour <= 9:  # 早高峰
            factor += 0.25
        elif 17 <= hour <= 19:  # 晚高峰
            factor += 0.20
        
        # 周末效应
        if weekday in [4, 5, 6]:  # 周五、周六、周日
            factor += 0.15
        
        # 深夜/清晨航班更准点
        if 0 <= hour <= 5:
            factor -= 0.10
        
        return factor
    
    def _get_season_factor(self, month, day):
        """获取季节因子"""
        factor = 0
        
        # 春运 (1-2月)
        if month in [1, 2]:
            factor += 0.20
        
        # 暑运 (7-8月)
        elif month in [7, 8]:
            factor += 0.15
        
        # 国庆黄金周 (10月1-7日)
        elif month == 10 and 1 <= day <= 7:
            factor += 0.25
        
        # 五一假期 (5月1-5日)
        elif month == 5 and 1 <= day <= 5:
            factor += 0.20
        
        return factor
    
    def _get_route_factor(self, origin, destination):
        """获取航线因子"""
        # 繁忙航线更容易延误
        busy_routes = [
            ('PEK', 'PVG'),  # 京沪线
            ('PEK', 'CAN'),  # 京广线
            ('PVG', 'CAN'),  # 沪穗线
            ('PEK', 'SZX'),  # 京深线
            ('PVG', 'CTU'),  # 沪蓉线
        ]
        
        if (origin, destination) in busy_routes:
            return 0.15
        elif (destination, origin) in busy_routes:
            return 0.10
        
        return 0.05
    
    def _analyze_delay_factors(self, airline, origin, destination, hour, weekday, month, day):
        """分析延误因素"""
        factors = []
        
        # 航空公司分析
        airline_stats = self.airline_delay_stats.get(airline, {})
        if airline_stats.get('delay_rate', 0) > 0.25:
            factors.append(f"{airline_stats.get('name', airline)}历史延误率较高")
        
        # 机场分析
        origin_stats = self.airport_delay_stats.get(origin, {})
        dest_stats = self.airport_delay_stats.get(destination, {})
        
        if origin_stats.get('delay_rate', 0) > 0.25:
            factors.append(f"{origin_stats.get('name', origin)}是繁忙机场")
        if dest_stats.get('delay_rate', 0) > 0.25:
            factors.append(f"{dest_stats.get('name', destination)}到达延误风险高")
        
        # 时间分析
        if 7 <= hour <= 9:
            factors.append("早高峰时段")
        elif 17 <= hour <= 19:
            factors.append("晚高峰时段")
        
        # 日期分析
        if month in [1, 2]:
            factors.append("春运期间")
        elif month in [7, 8]:
            factors.append("暑运期间")
        
        if weekday in [4, 5, 6]:
            factors.append("周末客流较大")
        
        # 如果因素太少，添加一般性分析
        if len(factors) < 2:
            factors.append("常规运行条件下")
        
        return factors
    
    def _prepare_features(self, flight_info):
        """为机器学习模型准备特征"""
        # 这里需要根据实际模型的特征要求来实现
        # 这是一个示例实现
        
        # 解析日期时间
        datetime_str = f"{flight_info['departure_date']} {flight_info['departure_time']}"
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        features = {
            'airline': flight_info['airline'],
            'origin': flight_info['origin'],
            'destination': flight_info['destination'],
            'hour': dt.hour,
            'month': dt.month,
            'weekday': dt.weekday(),
            'day': dt.day,
            'is_peak': 1 if 7 <= dt.hour <= 9 or 17 <= dt.hour <= 19 else 0,
            'is_weekend': 1 if dt.weekday() >= 5 else 0,
            'is_holiday_season': 1 if dt.month in [1, 2, 7, 8, 10] else 0
        }
        
        # 如果特征编码器可用，则进行编码
        if self.feature_encoder:
            return self.feature_encoder.transform([features])[0]
        
        # 否则返回原始特征（需要模型支持）
        return list(features.values())
    
    def _format_prediction_result(self, delay_prob, flight_info, model_type, importance=None, factors=None):
        """格式化预测结果"""
        # 计算预计延误时间
        if delay_prob < 0.3:
            estimated_delay = np.random.randint(0, 15)  # 0-15分钟
            risk_level = "低"
            confidence = 0.9
        elif delay_prob < 0.6:
            estimated_delay = np.random.randint(15, 45)  # 15-45分钟
            risk_level = "中"
            confidence = 0.8
        else:
            estimated_delay = np.random.randint(45, 120)  # 45-120分钟
            risk_level = "高"
            confidence = 0.7
        
        # 确定风险等级
        if delay_prob < 0.2:
            risk_level = "极低"
        elif delay_prob < 0.4:
            risk_level = "低"
        elif delay_prob < 0.6:
            risk_level = "中"
        elif delay_prob < 0.8:
            risk_level = "高"
        else:
            risk_level = "极高"
        
        # 获取航空公司信息
        airline_stats = self.airline_delay_stats.get(flight_info['airline'], {})
        airline_name = airline_stats.get('name', flight_info['airline'])
        
        # 获取机场信息
        origin_stats = self.airport_delay_stats.get(flight_info['origin'], {})
        dest_stats = self.airport_delay_stats.get(flight_info['destination'], {})
        
        origin_name = origin_stats.get('name', flight_info['origin'])
        dest_name = dest_stats.get('name', flight_info['destination'])
        
        # 如果没有提供因素，使用默认分析
        if factors is None:
            factors = self._analyze_delay_factors(
                flight_info['airline'],
                flight_info['origin'],
                flight_info['destination'],
                datetime.strptime(flight_info['departure_time'], '%H:%M').hour,
                datetime.strptime(flight_info['departure_date'], '%Y-%m-%d').weekday(),
                datetime.strptime(flight_info['departure_date'], '%Y-%m-%d').month,
                datetime.strptime(flight_info['departure_date'], '%Y-%m-%d').day
            )
        
        return {
            'delay_probability': round(delay_prob, 3),
            'estimated_delay_minutes': estimated_delay,
            'risk_level': risk_level,
            'confidence': confidence,
            'model_used': model_type,
            'factors': factors,
            'airline_info': {
                'code': flight_info['airline'],
                'name': airline_name,
                'historical_delay_rate': airline_stats.get('delay_rate', 0.2)
            },
            'route_info': {
                'origin': {
                    'code': flight_info['origin'],
                    'name': origin_name,
                    'delay_rate': origin_stats.get('delay_rate', 0.2)
                },
                'destination': {
                    'code': flight_info['destination'],
                    'name': dest_name,
                    'delay_rate': dest_stats.get('delay_rate', 0.2)
                }
            },
            'feature_importance': importance,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_default_prediction(self):
        """获取默认预测结果"""
        return {
            'delay_probability': 0.3,
            'estimated_delay_minutes': 15,
            'risk_level': "中",
            'confidence': 0.5,
            'model_used': "默认引擎",
            'factors': ["系统暂时无法分析具体因素"],
            'airline_info': {
                'code': 'UNKNOWN',
                'name': '未知',
                'historical_delay_rate': 0.2
            },
            'route_info': {
                'origin': {'code': 'UNK', 'name': '未知', 'delay_rate': 0.2},
                'destination': {'code': 'UNK', 'name': '未知', 'delay_rate': 0.2}
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_statistics(self):
        """获取预测引擎统计信息"""
        return {
            'airline_count': len(self.airline_delay_stats),
            'airport_count': len(self.airport_delay_stats),
            'ml_model_available': self.ml_model is not None,
            'prediction_method': '机器学习' if self.ml_model else '规则引擎',
            'avg_airline_delay_rate': round(
                sum(s['delay_rate'] for s in self.airline_delay_stats.values()) / 
                len(self.airline_delay_stats), 3
            )
        }

# 创建全局预测引擎实例
prediction_engine = DelayPredictionEngine(use_ml=True)

if __name__ == '__main__':
    # 测试预测引擎
    print("🧪 测试预测引擎...")
    
    test_flight = {
        'airline': 'CA',
        'flight_number': 'CA1234',
        'origin': 'PEK',
        'destination': 'PVG',
        'departure_date': '2024-07-15',
        'departure_time': '18:30'
    }
    
    result = prediction_engine.predict(test_flight)
    
    print(f"\n📊 预测结果:")
    print(f"  航班: {test_flight['airline']}{test_flight['flight_number']}")
    print(f"  航线: {test_flight['origin']} → {test_flight['destination']}")
    print(f"  时间: {test_flight['departure_date']} {test_flight['departure_time']}")
    print(f"  延误概率: {result['delay_probability']*100:.1f}%")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  预计延误: {result['estimated_delay_minutes']} 分钟")
    print(f"  使用模型: {result['model_used']}")
    print(f"  影响因素: {', '.join(result['factors'][:3])}")
    
    stats = prediction_engine.get_statistics()
    print(f"\n📈 引擎统计:")
    print(f"  航空公司: {stats['airline_count']} 家")
    print(f"  机场: {stats['airport_count']} 个")
    print(f"  机器学习模型: {'可用' if stats['ml_model_available'] else '不可用'}")
    print(f"  平均延误率: {stats['avg_airline_delay_rate']*100:.1f}%")