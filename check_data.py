import pandas as pd
import os

print("=" * 60)
print("📊 检查真实航班数据文件")
print("=" * 60)

# 检查文件是否存在
data_file = 'real_flight_data.xlsx'
if os.path.exists(data_file):
    print(f"✅ 找到文件: {data_file}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(data_file)
        
        print(f"\n📄 数据基本信息:")
        print(f"  行数: {len(df)}")
        print(f"  列数: {len(df.columns)}")
        
        print(f"\n📋 列名列表:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. '{col}' (数据类型: {df[col].dtype})")
        
        print(f"\n🔍 前5行数据:")
        print(df.head())
        
        print(f"\n📈 数据统计:")
        print(df.describe())
        
        print(f"\n❓ 缺失值统计:")
        print(df.isnull().sum())
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        
else:
    print(f"❌ 文件不存在: {data_file}")
    print("请确保 real_flight_data.xlsx 文件在 data 文件夹中")

print("\n" + "=" * 60)
input("按 Enter 键退出...")