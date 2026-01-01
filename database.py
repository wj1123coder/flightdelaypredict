#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
提供JSON文件存储功能
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_type: str = 'json'):
        """
        初始化数据库管理器
        
        Args:
            db_type: 数据库类型，'json' 或 'sqlite'
        """
        self.db_type = db_type
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        if db_type == 'sqlite':
            self.db_path = os.path.join(self.data_dir, 'flight_delay.db')
            self._init_sqlite_db()
        else:
            self.history_file = os.path.join(self.data_dir, 'prediction_history.json')
            self.stats_file = os.path.join(self.data_dir, 'system_stats.json')
    
    def _init_sqlite_db(self):
        """初始化SQLite数据库"""
        if not os.path.exists(self.db_path):
            print(f"📦 创建SQLite数据库: {self.db_path}")
            self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 预测历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                airline TEXT NOT NULL,
                flight_number TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                delay_probability REAL NOT NULL,
                estimated_delay INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                confidence REAL NOT NULL,
                model_used TEXT NOT NULL,
                user_ip TEXT,
                metadata TEXT
            )
        ''')
        
        # 系统统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_predictions INTEGER DEFAULT 0,
                total_delayed INTEGER DEFAULT 0,
                total_on_time INTEGER DEFAULT 0,
                avg_delay_probability REAL DEFAULT 0,
                most_predicted_airline TEXT,
                most_predicted_route TEXT,
                peak_hour TEXT
            )
        ''')
        
        # 用户反馈表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                timestamp TEXT NOT NULL,
                flight_number TEXT,
                actual_delay INTEGER,
                accuracy_rating INTEGER,
                comments TEXT,
                user_ip TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_prediction(self, flight_data: Dict[str, Any], 
                       prediction: Dict[str, Any],
                       user_ip: str = None,
                       metadata: Dict[str, Any] = None) -> Optional[int]:
        """
        保存预测记录
        
        Args:
            flight_data: 航班数据
            prediction: 预测结果
            user_ip: 用户IP地址
            metadata: 额外元数据
            
        Returns:
            记录ID或None
        """
        if self.db_type == 'sqlite':
            return self._save_to_sqlite(flight_data, prediction, user_ip, metadata)
        else:
            return self._save_to_json(flight_data, prediction, user_ip, metadata)
    
    def _save_to_sqlite(self, flight_data, prediction, user_ip, metadata):
        """保存到SQLite数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO predictions 
                (timestamp, airline, flight_number, origin, destination, 
                 departure_date, departure_time, delay_probability, 
                 estimated_delay, risk_level, confidence, model_used, user_ip, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                flight_data.get('airline', ''),
                flight_data.get('flight_number', ''),
                flight_data.get('origin', ''),
                flight_data.get('destination', ''),
                flight_data.get('departure_date', ''),
                flight_data.get('departure_time', ''),
                prediction.get('delay_probability', 0),
                prediction.get('estimated_delay_minutes', 0),
                prediction.get('risk_level', '低'),
                prediction.get('confidence', 0.5),
                prediction.get('model_used', '规则引擎'),
                user_ip,
                json.dumps(metadata) if metadata else None
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # 更新统计信息
            self._update_daily_stats()
            
            print(f"✅ SQLite记录保存成功，ID: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ SQLite保存失败: {e}")
            return None
    
    def _save_to_json(self, flight_data, prediction, user_ip, metadata):
        """保存到JSON文件"""
        try:
            # 读取现有历史
            history = self.load_history()
            
            # 创建新记录
            record = {
                "id": len(history) + 1,
                "timestamp": datetime.now().isoformat(),
                "flight_data": flight_data,
                "prediction": prediction,
                "user_ip": user_ip or "127.0.0.1",
                "metadata": metadata or {}
            }
            
            # 添加到历史
            history.append(record)
            
            # 只保留最近1000条记录
            if len(history) > 1000:
                history = history[-1000:]
            
            # 保存到文件
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            # 更新统计
            self._update_json_stats(record)
            
            print(f"✅ JSON记录保存成功，ID: {record['id']}")
            return record['id']
            
        except Exception as e:
            print(f"❌ JSON保存失败: {e}")
            return None
    
    def load_history(self, limit: int = None) -> List[Dict]:
        """加载预测历史"""
        if self.db_type == 'sqlite':
            return self._load_from_sqlite(limit)
        else:
            return self._load_from_json(limit)
    
    def _load_from_sqlite(self, limit):
        """从SQLite加载"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM predictions 
                ORDER BY timestamp DESC
            '''
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            history = []
            for row in rows:
                record = dict(row)
                # 解析metadata
                if record.get('metadata'):
                    record['metadata'] = json.loads(record['metadata'])
                history.append(record)
            
            return history
            
        except Exception as e:
            print(f"❌ SQLite加载失败: {e}")
            return []
    
    def _load_from_json(self, limit):
        """从JSON文件加载"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # 按时间戳排序（最新在前）
                history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                return history[:limit] if limit else history
        except:
            pass
        return []
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """获取最近的预测记录"""
        return self.load_history(limit)
    
    def get_today_stats(self) -> Dict[str, Any]:
        """获取今日统计"""
        today = datetime.now().date().isoformat()
        
        if self.db_type == 'sqlite':
            return self._get_sqlite_today_stats(today)
        else:
            return self._get_json_today_stats(today)
    
    def _get_sqlite_today_stats(self, today):
        """从SQLite获取今日统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 今日预测总数
            cursor.execute('''
                SELECT COUNT(*) FROM predictions 
                WHERE date(timestamp) = ?
            ''', (today,))
            total = cursor.fetchone()[0]
            
            # 延误预测数
            cursor.execute('''
                SELECT COUNT(*) FROM predictions 
                WHERE date(timestamp) = ? AND delay_probability > 0.5
            ''', (today,))
            delayed = cursor.fetchone()[0]
            
            # 平均延误概率
            cursor.execute('''
                SELECT AVG(delay_probability) FROM predictions 
                WHERE date(timestamp) = ?
            ''', (today,))
            avg_prob = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'date': today,
                'total': total,
                'delayed': delayed,
                'on_time': total - delayed,
                'avg_delay_prob': round(avg_prob, 3)
            }
            
        except Exception as e:
            print(f"❌ 获取SQLite统计失败: {e}")
            return {
                'date': today,
                'total': 0,
                'delayed': 0,
                'on_time': 0,
                'avg_delay_prob': 0
            }
    
    def _get_json_today_stats(self, today):
        """从JSON获取今日统计"""
        history = self.load_history()
        
        # 筛选今日记录
        today_predictions = [
            p for p in history 
            if p.get('timestamp', '').startswith(today)
        ]
        
        # 统计
        delayed_count = len([
            p for p in today_predictions 
            if p.get('prediction', {}).get('delay_probability', 0) > 0.5
        ])
        
        total = len(today_predictions)
        avg_prob = sum(
            p.get('prediction', {}).get('delay_probability', 0) 
            for p in today_predictions
        ) / max(total, 1)
        
        return {
            'date': today,
            'total': total,
            'delayed': delayed_count,
            'on_time': total - delayed_count,
            'avg_delay_prob': round(avg_prob, 3)
        }
    
    def _update_daily_stats(self):
        """更新每日统计（SQLite）"""
        if self.db_type != 'sqlite':
            return
        
        today = datetime.now().date().isoformat()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查今日统计是否存在
            cursor.execute('SELECT id FROM statistics WHERE date = ?', (today,))
            exists = cursor.fetchone()
            
            # 获取今日数据
            stats = self._get_sqlite_today_stats(today)
            
            if exists:
                # 更新现有记录
                cursor.execute('''
                    UPDATE statistics SET 
                    total_predictions = ?,
                    total_delayed = ?,
                    total_on_time = ?,
                    avg_delay_probability = ?
                    WHERE date = ?
                ''', (
                    stats['total'],
                    stats['delayed'],
                    stats['on_time'],
                    stats['avg_delay_prob'],
                    today
                ))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO statistics 
                    (date, total_predictions, total_delayed, 
                     total_on_time, avg_delay_probability)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    today,
                    stats['total'],
                    stats['delayed'],
                    stats['on_time'],
                    stats['avg_delay_prob']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 更新每日统计失败: {e}")
    
    def _update_json_stats(self, new_record):
        """更新JSON统计"""
        try:
            # 加载现有统计
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {}
            
            today = datetime.now().date().isoformat()
            
            # 获取今日统计
            today_stats = self._get_json_today_stats(today)
            
            # 更新统计
            stats[today] = today_stats
            
            # 只保留最近30天的统计
            dates = list(stats.keys())
            dates.sort(reverse=True)
            if len(dates) > 30:
                for old_date in dates[30:]:
                    del stats[old_date]
            
            # 保存统计文件
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"❌ 更新JSON统计失败: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        if self.db_type == 'sqlite':
            return self._get_sqlite_system_stats()
        else:
            return self._get_json_system_stats()
    
    def _get_sqlite_system_stats(self):
        """获取SQLite系统统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总预测数
            cursor.execute('SELECT COUNT(*) FROM predictions')
            total = cursor.fetchone()[0]
            
            # 总延误预测数
            cursor.execute('SELECT COUNT(*) FROM predictions WHERE delay_probability > 0.5')
            total_delayed = cursor.fetchone()[0]
            
            # 平均延误概率
            cursor.execute('SELECT AVG(delay_probability) FROM predictions')
            avg_prob = cursor.fetchone()[0] or 0
            
            # 最常预测的航空公司
            cursor.execute('''
                SELECT airline, COUNT(*) as count 
                FROM predictions 
                GROUP BY airline 
                ORDER BY count DESC 
                LIMIT 3
            ''')
            top_airlines = [{'airline': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # 最常预测的航线
            cursor.execute('''
                SELECT origin, destination, COUNT(*) as count 
                FROM predictions 
                GROUP BY origin, destination 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            top_routes = [{'route': f"{row[0]}-{row[1]}", 'count': row[2]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_predictions': total,
                'total_delayed': total_delayed,
                'total_on_time': total - total_delayed,
                'avg_delay_probability': round(avg_prob, 3),
                'top_airlines': top_airlines,
                'top_routes': top_routes,
                'database_type': 'sqlite'
            }
            
        except Exception as e:
            print(f"❌ 获取系统统计失败: {e}")
            return self._get_default_stats()
    
    def _get_json_system_stats(self):
        """获取JSON系统统计"""
        history = self.load_history()
        
        if not history:
            return self._get_default_stats()
        
        total = len(history)
        total_delayed = len([
            p for p in history 
            if p.get('prediction', {}).get('delay_probability', 0) > 0.5
        ])
        avg_prob = sum(
            p.get('prediction', {}).get('delay_probability', 0) 
            for p in history
        ) / max(total, 1)
        
        # 统计航空公司
        airline_counts = {}
        route_counts = {}
        
        for record in history:
            flight_data = record.get('flight_data', {})
            airline = flight_data.get('airline', '未知')
            origin = flight_data.get('origin', '')
            destination = flight_data.get('destination', '')
            
            airline_counts[airline] = airline_counts.get(airline, 0) + 1
            
            if origin and destination:
                route = f"{origin}-{destination}"
                route_counts[route] = route_counts.get(route, 0) + 1
        
        # 排序
        top_airlines = sorted(
            [{'airline': k, 'count': v} for k, v in airline_counts.items()],
            key=lambda x: x['count'], reverse=True
        )[:3]
        
        top_routes = sorted(
            [{'route': k, 'count': v} for k, v in route_counts.items()],
            key=lambda x: x['count'], reverse=True
        )[:5]
        
        return {
            'total_predictions': total,
            'total_delayed': total_delayed,
            'total_on_time': total - total_delayed,
            'avg_delay_probability': round(avg_prob, 3),
            'top_airlines': top_airlines,
            'top_routes': top_routes,
            'database_type': 'json'
        }
    
    def _get_default_stats(self):
        """获取默认统计"""
        return {
            'total_predictions': 0,
            'total_delayed': 0,
            'total_on_time': 0,
            'avg_delay_probability': 0,
            'top_airlines': [],
            'top_routes': [],
            'database_type': self.db_type
        }
    
    def save_feedback(self, prediction_id: int, 
                     actual_delay: int, 
                     accuracy_rating: int,
                     comments: str = None,
                     user_ip: str = None) -> bool:
        """保存用户反馈"""
        try:
            if self.db_type == 'sqlite':
                return self._save_feedback_sqlite(prediction_id, actual_delay, 
                                                 accuracy_rating, comments, user_ip)
            else:
                return self._save_feedback_json(prediction_id, actual_delay,
                                               accuracy_rating, comments, user_ip)
        except Exception as e:
            print(f"❌ 保存反馈失败: {e}")
            return False
    
    def _save_feedback_sqlite(self, prediction_id, actual_delay, 
                             accuracy_rating, comments, user_ip):
        """保存反馈到SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取航班号
            cursor.execute('SELECT flight_number FROM predictions WHERE id = ?', (prediction_id,))
            result = cursor.fetchone()
            flight_number = result[0] if result else None
            
            cursor.execute('''
                INSERT INTO feedback 
                (prediction_id, timestamp, flight_number, actual_delay, 
                 accuracy_rating, comments, user_ip)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_id,
                datetime.now().isoformat(),
                flight_number,
                actual_delay,
                accuracy_rating,
                comments,
                user_ip
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ SQLite反馈保存失败: {e}")
            return False
    
    def _save_feedback_json(self, prediction_id, actual_delay, 
                           accuracy_rating, comments, user_ip):
        """保存反馈到JSON"""
        try:
            feedback_file = os.path.join(self.data_dir, 'user_feedback.json')
            
            # 读取现有反馈
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            else:
                feedbacks = []
            
            # 创建新反馈
            feedback = {
                "id": len(feedbacks) + 1,
                "prediction_id": prediction_id,
                "timestamp": datetime.now().isoformat(),
                "actual_delay": actual_delay,
                "accuracy_rating": accuracy_rating,
                "comments": comments,
                "user_ip": user_ip
            }
            
            feedbacks.append(feedback)
            
            # 保存
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ JSON反馈保存失败: {e}")
            return False
    
    def export_data(self, export_type: str = 'json') -> str:
        """导出数据"""
        try:
            if export_type == 'json':
                return self._export_json()
            elif export_type == 'csv':
                return self._export_csv()
            else:
                raise ValueError(f"不支持的导出类型: {export_type}")
        except Exception as e:
            print(f"❌ 数据导出失败: {e}")
            return ""
    
    def _export_json(self) -> str:
        """导出为JSON"""
        history = self.load_history()
        stats = self.get_system_stats()
        
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_records": len(history),
                "database_type": self.db_type
            },
            "statistics": stats,
            "history": history
        }
        
        export_file = os.path.join(self.data_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return export_file
    
    def _export_csv(self) -> str:
        """导出为CSV"""
        import csv
        
        history = self.load_history()
        if not history:
            return ""
        
        export_file = os.path.join(self.data_dir, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        # 提取所有可能的字段
        fieldnames = set()
        for record in history:
            # 基本字段
            fieldnames.update(['id', 'timestamp'])
            # 航班数据字段
            if 'flight_data' in record:
                fieldnames.update([f"flight_{k}" for k in record['flight_data'].keys()])
            # 预测字段
            if 'prediction' in record:
                fieldnames.update([f"prediction_{k}" for k in record['prediction'].keys()])
        
        fieldnames = list(fieldnames)
        fieldnames.sort()
        
        with open(export_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in history:
                row = {'id': record.get('id'), 'timestamp': record.get('timestamp')}
                
                # 添加航班数据
                flight_data = record.get('flight_data', {})
                for k, v in flight_data.items():
                    row[f"flight_{k}"] = v
                
                # 添加预测数据
                prediction = record.get('prediction', {})
                for k, v in prediction.items():
                    if isinstance(v, (dict, list)):
                        row[f"prediction_{k}"] = json.dumps(v, ensure_ascii=False)
                    else:
                        row[f"prediction_{k}"] = v
                
                writer.writerow(row)
        
        return export_file
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            
            if self.db_type == 'sqlite':
                self._cleanup_sqlite(cutoff_date)
            else:
                self._cleanup_json(cutoff_date)
            
            print(f"✅ 清理{days}天前的数据完成")
            
        except Exception as e:
            print(f"❌ 数据清理失败: {e}")
    
    def _cleanup_sqlite(self, cutoff_date):
        """清理SQLite旧数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 删除旧预测记录
        cursor.execute('DELETE FROM predictions WHERE date(timestamp) < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        
        # 删除关联的反馈
        cursor.execute('''
            DELETE FROM feedback 
            WHERE prediction_id IN (
                SELECT id FROM predictions WHERE date(timestamp) < ?
            )
        ''', (cutoff_date,))
        
        # 删除旧统计
        cursor.execute('DELETE FROM statistics WHERE date < ?', (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        print(f"📊 清理SQLite数据: 删除{deleted_count}条预测记录")
    
    def _cleanup_json(self, cutoff_date):
        """清理JSON旧数据"""
        # 清理预测历史
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            new_history = [
                record for record in history 
                if record.get('timestamp', '').split('T')[0] >= cutoff_date
            ]
            
            deleted_count = len(history) - len(new_history)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(new_history, f, ensure_ascii=False, indent=2)
            
            print(f"📊 清理JSON数据: 删除{deleted_count}条预测记录")
        
        # 清理统计文件
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            new_stats = {
                k: v for k, v in stats.items() 
                if k >= cutoff_date
            }
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(new_stats, f, ensure_ascii=False, indent=2)

# 创建全局实例
db_manager = DatabaseManager(db_type='json')  # 默认使用JSON存储

if __name__ == '__main__':
    # 测试数据库功能
    print("🧪 测试数据库功能...")
    
    # 测试数据
    test_flight_data = {
        'airline': 'CA',
        'flight_number': 'CA1234',
        'origin': 'PEK',
        'destination': 'PVG',
        'departure_date': '2024-01-15',
        'departure_time': '14:30'
    }
    
    test_prediction = {
        'delay_probability': 0.65,
        'estimated_delay_minutes': 45,
        'risk_level': '高',
        'confidence': 0.85,
        'model_used': '规则引擎'
    }
    
    # 保存测试记录
    record_id = db_manager.save_prediction(test_flight_data, test_prediction)
    print(f"📝 保存记录成功，ID: {record_id}")
    
    # 加载历史记录
    history = db_manager.get_recent_predictions(5)
    print(f"📊 最近5条记录: {len(history)} 条")
    
    # 获取今日统计
    today_stats = db_manager.get_today_stats()
    print(f"📈 今日统计: {today_stats}")
    
    # 获取系统统计
    system_stats = db_manager.get_system_stats()
    print(f"🏢 系统统计: {system_stats['total_predictions']} 条总记录")
    
    print("✅ 数据库测试完成")