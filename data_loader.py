import pandas as pd
import numpy as np
import os

class FlightDataLoader:
    def __init__(self):
        self.data_dir = os.path.dirname(os.path.abspath(__file__))
        
    def load_real_data(self, file_name='real_flight_data.xlsx'):
        """加载真实航班数据"""
        file_path = os.path.join(self.data_dir, file_name)
        
        try:
            if os.path.exists(file_path):
                # 从Excel加载
                df = pd.read_excel(file_path)
                print(f"✅ 成功加载真实航班数据，共 {len(df)} 条记录")
                return df
            else:
                print(f"⚠️ 未找到真实数据文件，创建示例数据...")
                return self.create_sample_data()
                
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """创建示例数据"""
        np.random.seed(42)
        
        # 生成1000条示例数据
        airlines = ['CA', 'MU', 'CZ', 'HU', 'ZH', 'MF']
        airports = ['PEK', 'PVG', 'CAN', 'SZX', 'TFU', 'CKG', 'XIY', 'HGH', 'NKG']
        weathers = ['晴', '多云', '雨', '雾', '雪']
        
        data = []
        for i in range(1000):
            date = f"2024-{np.random.randint(1, 13):02d}-{np.random.randint(1, 29):02d}"
            airline = np.random.choice(airlines)
            flight_num = f"{airline}{np.random.randint(1000, 9999)}"
            origin = np.random.choice(airports)
            destination = np.random.choice([a for a in airports if a != origin])
            
            planned_hour = np.random.randint(6, 22)
            planned_minute = np.random.choice([0, 15, 30, 45])
            planned_time = f"{planned_hour:02d}:{planned_minute:02d}"
            
            # 模拟延误（基于某些规则）
            base_delay = 0
            if planned_hour in [7, 8, 18, 19]:  # 高峰时段
                base_delay += np.random.randint(10, 30)
            if origin in ['PEK', 'PVG', 'CAN']:  # 繁忙机场
                base_delay += np.random.randint(5, 20)
            if np.random.random() < 0.3:  # 30%概率天气影响
                base_delay += np.random.randint(15, 60)
                
            actual_delay = max(0, base_delay + np.random.randint(-10, 20))
            actual_time = self.add_minutes(planned_time, actual_delay)
            
            weather = np.random.choice(weathers)
            is_holiday = '是' if np.random.random() < 0.2 else '否'
            
            data.append([
                date, airline, flight_num, origin, destination,
                planned_time, actual_time, actual_delay,
                weather, is_holiday
            ])
        
        df = pd.DataFrame(data, columns=[
            '航班日期', '航空公司', '航班号', '出发机场', '到达机场',
            '计划起飞时间', '实际起飞时间', '延误分钟',
            '天气状况', '节假日'
        ])
        
        # 保存到文件
        save_path = os.path.join(self.data_dir, 'flight_data_sample.xlsx')
        df.to_excel(save_path, index=False)
        print(f"✅ 已生成示例数据到: {save_path}")
        
        return df
    
    def add_minutes(self, time_str, minutes):
        """为时间添加分钟"""
        from datetime import datetime, timedelta
        time_obj = datetime.strptime(time_str, '%H:%M')
        new_time = time_obj + timedelta(minutes=minutes)
        return new_time.strftime('%H:%M')
    
    def get_statistics(self, df):
        """获取数据统计"""
        stats = {
            '总记录数': len(df),
            '平均延误': f"{df['延误分钟'].mean():.1f} 分钟",
            '准点率': f"{(df['延误分钟'] <= 15).mean()*100:.1f}%",
            '最繁忙航线': df.groupby(['出发机场', '到达机场']).size().idxmax(),
            '延误最严重航空公司': df.groupby('航空公司')['延误分钟'].mean().idxmax()
        }
        return stats

# 测试数据加载
if __name__ == '__main__':
    loader = FlightDataLoader()
    df = loader.load_real_data()
    stats = loader.get_statistics(df)
    
    print("\n📊 航班数据统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 添加这行代码，防止窗口闪退
    input("\n✅ 数据加载完成！按 Enter 键退出...")