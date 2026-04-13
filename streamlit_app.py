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
            status = element.get('status')
            if status == 'OK':
                return element['distance']['text'], element['duration']['text']
            elif status == 'ZERO_RESULTS':
                return "路徑不通", "無合適交通工具"
        return "未知距離", "無法計算"
    except Exception:
        return "連線失敗", "網路錯誤"

# --- 載入資料庫 ---
@st.cache_data
def load_data():
    try:
        # 讀取你的 Scenic_Spot_C_f.csv
        df = pd.read_csv('Scenic_Spot_C_f.csv')
        return df
    except Exception as e:
        st.error(f"❌ 讀取 CSV 失敗: {e}")
        return None

df = load_data()

# --- UI 介面設定 ---
st.set_page_config(page_title="全台智能旅遊助手 V3.0", layout="wide")
st.title("全台智能旅遊助手 V3.0 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    
    # 【核心修正】加入全台灣完整 22 縣市清單
    city_options = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "基隆市", "新竹縣", "新竹市", "苗栗縣", "彰化縣", "南投縣",
        "雲林縣", "嘉義縣", "嘉義市", "屏東縣", "宜蘭縣", "花蓮縣",
        "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    city = st.selectbox("選擇目的縣市", city_options)
    
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    st.markdown("---")
    # 修正：起點與住宿點完全分開的欄位
    start_point = st.text_input("🚩 設定第一天出發起點", "宜蘭火車站")
    hotel_addr = st.text_input("🏨 設定每日住宿/終點", "伯斯飯店")

# --- 核心邏輯 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        # 根據地址 (Add 欄位) 篩選縣市景點
        if 'Add' in df.columns:
            filtered_df = df[df['Add'].str.contains(city, na=False)]
            
            if filtered_df.empty:
                st.warning(f"目前資料庫中找不到包含「{city}」的景點。")
            else:
                st.header(f"📍 為您規劃的 {city} {days} 日遊")
                st.info(f"🚩 出發地：{start_point} | 🏨 每日住宿/終點：{hotel_addr}")

                for day in range(1, days + 1):
                    with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                        # 隨機抽取 3 個景點
                        sample_count = min(len(filtered_df), 3)
                        daily_spots = filtered_df.sample(sample_count)['Name'].tolist()
                        
                        # 第一天從「起點」出發，其餘天數從「飯店」出發
                        current_origin = start_point if day == 1 else hotel_addr
                        
                        for i, spot in enumerate(daily_spots):
                            # 自動補強搜尋關鍵字，提高 Google Maps 命中率
                            search_dest = f"{city}{spot}" if not spot.startswith(city) else spot
                            
                            dist, travel_time = get_google_travel_info(current_origin, search_dest, transport_mode)
                            
                            st.markdown(f"#### 第 {i+1} 站：{spot}")
                            st.write(f"⏱️ 從 **{current_origin}** 出發 ➔ 移動約 **{dist}** (預估耗時 **{travel_time}**)")
                            st.markdown("---")
                            
                            current_origin = spot # 更新下一站起點
                        
                        # 每天結束回到「住宿點」
                        dist_back, time_back = get_google_travel_info(current_origin, hotel_addr, transport_mode)
                        st.success(f"🌙 結束行程：返回住宿點 **{hotel_addr}** (約需 {time_back})")
        else:
            st.error("❌ 資料庫格式不符，找不到 'Add' 欄位。")
