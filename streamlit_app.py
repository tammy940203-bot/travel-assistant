import streamlit as st
import pandas as pd
import requests
import random

# 1. 安全金鑰
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！")
    st.stop()

# 2. Google Maps API 函式
def get_google_travel_info(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "language": "zh-TW", "key": API_KEY}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
        return "未知距離", "無法計算"
    except:
        return "連線失敗", "網路錯誤"

@st.cache_data
def load_data():
    try:
        return pd.read_csv('Scenic_Spot_C_f.csv')
    except:
        return None

df = load_data()

# --- UI 介面 ---
st.set_page_config(page_title="全台智能旅遊助手 V3.2", layout="wide")
st.title("全台智能旅遊助手 V3.2 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city_options = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "宜蘭縣", "花蓮縣", "屏東縣"]
    city = st.selectbox("選擇目的縣市", city_options)
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    start_point = st.text_input("🚩 第一天出發起點", "宜蘭火車站")
    hotel_addr = st.text_input("🏨 每日住宿/終點", "伯斯飯店")

# --- 核心邏輯 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        # 第一步：初步篩選縣市
        city_df = df[df['Add'].str.contains(city, na=False)].copy()

        # 第二步：【排除黑名單】排除書店、補習班等雜項
        blacklist = ['書店', '書局', '圖書館', '補習班', '藥局', '診所', '服務處', '辦事處']
        pattern = '|'.join(blacklist)
        filtered_df = city_df[~city_df['Name'].str.contains(pattern, na=False)]

        if filtered_df.empty:
            st.warning(f"目前資料庫中找不到符合條件的景點。")
        else:
            st.header(f"📍 為您規劃的 {city} {days} 日遊")
            
            # 第三步：【防止重複】建立一個全域使用的 Set
            used_spots = set()

            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    # 每次抽樣前，先過濾掉已經去過的點
                    available_df = filtered_df[~filtered_df['Name'].isin(used_spots)]
                    
                    if available_df.empty:
                        st.write("已無更多景點。")
                        break

                    # 隨機抽取 3 個點
                    sample_count = min(len(available_df), 3)
                    daily_selection = available_df.sample(sample_count)
                    daily_spots = daily_selection['Name'].tolist()
                    
                    # 將這 3 個點加入「已使用」名單
                    for s in daily_spots:
                        used_spots.add(s)

                    current_origin = start_point if day == 1 else hotel_addr
                    
                    for i, spot in enumerate(daily_spots):
                        search_dest = f"{city}{spot}"
                        dist, travel_time = get_google_travel_info(current_origin, search_dest, transport_mode)
                        
                        st.markdown(f"#### 第 {idx if 'idx' in locals() else i+1} 站：{spot}")
                        st.write(f"⏱️ 從 **{current_origin}** ➔ **{spot}** (距離 {dist}，約需 {travel_time})")
                        st.markdown("---")
                        current_origin = spot
                    
                    # 回飯店
                    _, time_back = get_google_travel_info(current_origin, hotel_addr, transport_mode)
                    st.success(f"🌙 結束行程：返回住宿點 **{hotel_addr}** (約需 {time_back})")
