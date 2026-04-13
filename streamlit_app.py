import streamlit as st
import pandas as pd
import requests
import random

# 1. 從 Secrets 讀取金鑰
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 設定 MAPS_API_KEY")
    st.stop()

# 2. Google Maps API 請求函式
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
            status = element.get('status')
            if status == 'OK':
                return element['distance']['text'], element['duration']['text']
            elif status == 'ZERO_RESULTS':
                return "路徑不通", "無大眾運輸工具"
        return "未知距離", "無法計算"
    except:
        return "連線失敗", "網路異常"

# 3. 載入資料
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Scenic_Spot_C_f.csv')
        return df
    except Exception as e:
        st.error(f"❌ 讀取 CSV 失敗: {e}")
        return None

df = load_data()

# --- UI 介面 ---
st.set_page_config(page_title="智能旅遊助手 V3.0", layout="wide")
st.title("全台智能旅遊助手 V3.0 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["宜蘭縣", "南投縣", "臺北市", "臺中市", "高雄市", "花蓮縣", "桃園市"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    st.markdown("---")
    # 這裡將起點與住宿點欄位完全分開
    start_point = st.text_input("🚩 設定第一天出發點", "宜蘭火車站")
    hotel_addr = st.text_input("🏨 設定每日住宿點", "伯斯飯店")

# --- 生成邏輯 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        if 'Add' in df.columns:
            filtered_df = df[df['Add'].str.contains(city, na=False)]
            
            if filtered_df.empty:
                st.warning(f"目前資料中找不到「{city}」的景點。")
            else:
                st.header(f"📍 為您規劃的 {city} {days} 日遊")
                st.info(f"🚩 起點：{start_point} | 🏨 住宿：{hotel_addr}")

                for day in range(1, days + 1):
                    with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                        # 隨機選景點
                        sample_count = min(len(filtered_df), 3)
                        daily_spots = filtered_df.sample(sample_count)['Name'].tolist()
                        
                        # 第一天從起點出發，之後每天從飯店出發
                        current_origin = start_point if day == 1 else hotel_addr
                        
                        for i, spot in enumerate(daily_spots):
                            # 自動補強搜尋關鍵字，降低「無法計算」機率
                            search_dest = f"{city}{spot}" if not spot.startswith(city) else spot
                            dist, travel_time = get_google_travel_info(current_origin, search_dest, transport_mode)
                            
                            st.markdown(f"#### 第 {i+1} 站：{spot}")
                            st.caption(f"🏁 從 **{current_origin}** 出發 ➔ 移動約 **{dist}** (預估 **{travel_time}**)")
                            st.markdown("---")
                            current_origin = spot
                        
                        # 每天最後回住宿點
                        dist_back, time_back = get_google_travel_info(current_origin, hotel_addr, transport_mode)
                        st.success(f"🌙 結束行程：返回住宿點 **{hotel_addr}** (約需 {time_back})")
        else:
            # 修正了這裡原本導致 SyntaxError 的漏寫引號問題
            st.error("❌ 資料庫格式錯誤，找不到 'Add' 欄位。")
