import streamlit as st
import pandas as pd
import requests
import random

# 1. 從 Secrets 安全讀取金鑰
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Cloud 的 Secrets 中設定 MAPS_API_KEY")
    st.stop()

# 2. 定義 Google Maps 距離矩陣函式
def get_google_travel_info(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "language": "zh-TW",
        "key": API_KEY
    }
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                return element['distance']['text'], element['duration']['text']
        return "未知距離", "無法計算"
    except:
        return "連線失敗", "請檢查網路"

# --- 載入資料庫 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Scenic_Spot_C_f.csv')
        return df
    except Exception as e:
        st.error(f"❌ 讀取 CSV 失敗: {e}")
        return None

df = load_data()

# --- UI 介面設定 ---
st.set_page_config(page_title="智能旅遊助手 V3.0", layout="wide")
st.title("全台智能旅遊助手 V3.0 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    
    city_options = ["宜蘭縣", "南投縣", "臺北市", "臺中市", "高雄市", "花蓮縣", "桃園市"]
    city = st.selectbox("選擇目的縣市", city_options)
    
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    # 這裡就是你的「起點」設定
    start_point = st.text_input("📍 設定每日出發起點 (例如：宜蘭火車站或飯店名稱)", "宜蘭火車站")

# --- 核心邏輯 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        if 'Add' in df.columns:
            filtered_df = df[df['Add'].str.contains(city, na=False)]
            
            if filtered_df.empty:
                st.warning(f"目前資料庫中找不到包含「{city}」的景點。")
            else:
                st.header(f"📍 為您規劃的 {city} {days} 日遊")
                st.info(f"🚩 每日出發起點：{start_point}")

                for day in range(1, days + 1):
                    with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                        sample_count = min(len(filtered_df), 3)
                        daily_spots = filtered_df.sample(sample_count)['Name'].tolist()
                        
                        # 每一天的起點
                        current_origin = start_point
                        
                        for i, spot in enumerate(daily_spots):
                            dist, travel_time = get_google_travel_info(current_origin, spot, transport_mode)
                            
                            # 顯示目前位置與目標站點
                            st.markdown(f"**第 {i+1} 站：{spot}**")
                            st.caption(f"🏁 從 **{current_origin}** 出發 ➔ 移動約 **{dist}** (預估耗時 **{travel_time}**)")
                            st.markdown("---")
                            
                            # 更新下一站的起點
                            current_origin = spot
                        
                        # 回程顯示
                        dist_back, time_back = get_google_travel_info(current_origin, start_point, transport_mode)
                        st.success(f"🌙 結束行程：返回起點 **{start_point}** (約需 {time_back})")
        else:
            st.error("CSV 格式不符，找不到 'Add' 欄位。")
