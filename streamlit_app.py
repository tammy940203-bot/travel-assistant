import streamlit as st
import pandas as pd
import requests
import random

# 1. 從 Secrets 安全讀取金鑰 (請確保標籤為 MAPS_API_KEY)
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Cloud 的 Secrets 中設定 MAPS_API_KEY")
    st.stop()

# 2. 定義 Google Maps 距離矩陣函式 (優化錯誤處理)
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
                return "路徑不通", "無大眾工具或路網"
            elif status == 'NOT_FOUND':
                return "地點不明", "找不到此地"
        return "未知距離", "無法計算"
    except Exception:
        return "連線失敗", "網路錯誤"

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
    
    # 修正：起點與住宿點完全分開的欄位
    start_point = st.text_input("🚩 設定第一天出發起點 (例如：宜蘭火車站)", "宜蘭火車站")
    hotel_addr = st.text_input("🏨 設定每日住宿/終點 (例如：伯斯飯店)", "伯斯飯店")

# --- 核心邏輯 ---
if st.
