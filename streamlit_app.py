import streamlit as st
import pandas as pd
import numpy as np

# 設定頁面與快取
st.set_page_config(page_title="全台智能旅遊助手 V2", layout="wide")

@st.cache_data
def load_and_clean_data():
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    # 建立標準縣市
    taiwan_cities = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"]
    def get_city(addr):
        for c in taiwan_cities:
            if c in str(addr): return c
        return None
    df['City'] = df['Add'].apply(get_city)
    return df.dropna(subset=['City', 'Py', 'Px']), taiwan_cities

# 計算球面距離 (Haversine formula)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑 (km)
    dlat, dlon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

try:
    df, city_list = load_and_clean_data()
    available_cities = sorted(df['City'].unique())
except:
    st.error("資料讀取失敗，請確認檔案。")
    st.stop()

# UI 介面
st.title("智能旅遊助手：AI 動態排程模式 🚀")
with st.sidebar:
    st.header("參數設定")
    city = st.selectbox("目的地縣市", available_cities)
    days = st.slider("旅遊天數", 1, 3, 1) # 示範先以短程為主
    transport = st.radio("交通工具", ["大眾運輸", "自行開車"])

# 交通參數設定 (這就是你的緩衝時間模型)
speed = 40 if transport == "自行開車" else 25 # 公里/小時
buffer = 10 if transport == "自行開車" else 25 # 分鐘 (找車位 vs 候車)

if st.button("生成最順暢路線"):
    city_df = df[df['City'] == city].sample(min(len(df[df['City']==city]), 4)).reset_index()
    
    st.subheader(f"📍 {city} 優化行程表 (考量{transport}緩衝)")
    
    total_time = 0
    for i in range(len(city_df)):
        spot = city_df.iloc[i]
        
        # 顯示景點卡片
        with st.expander(f"第 {i+1} 站：{spot['Name']}", expanded=True):
            st.write(f"🏠 地址：{spot['Add']}")
            st.write(f"🕒 營業時間：{spot['Opentime']}")
            
            if i < len(city_df) - 1:
                next_spot = city_df.iloc[i+1]
                dist = haversine(spot['Py'], spot['Px'], next_spot['Py'], next_spot['Px'])
                # 計算真實含緩衝時間
                travel_min = (dist / speed) * 60 + buffer
                
                st.markdown(f"⬇️ **移動至下一站**：約 **{dist:.1f} 公里**")
                st.warning(f"🚗 建議交通：{transport} | 預估耗時：**{travel_min:.0f} 分鐘** (含 {buffer} 分鐘緩衝)")
