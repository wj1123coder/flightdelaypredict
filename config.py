import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'flight-delay-prediction-secret-key'
    MODEL_PATH = 'models/flight_delay_model.pkl'
    DATA_PATH = 'data/flights.csv'
    
    # 数据库配置
    DATABASE_URI = 'sqlite:///data/flight_predictions.db'
    
    # API配置
    CACHE_TIMEOUT = 300  # 5分钟缓存
    MAX_PREDICTIONS_PER_DAY = 1000
    
    # 航空公司颜色（用于图表）
    AIRLINE_COLORS = {
        'AA': '#1E88E5',  # 蓝色
        'DL': '#FFC107',  # 黄色
        'UA': '#E53935',  # 红色
        'WN': '#43A047',  # 绿色
        'B6': '#8E24AA',  # 紫色
        'NK': '#FB8C00'   # 橙色
    }