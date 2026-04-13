import streamlit as st
import pandas as pd
import requests
import random

# 1. 從 Secrets 安全讀取金鑰 (請確保 Streamlit 後台 Secrets 設定為 MAPS_API_KEY)
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
        "mode": mode,  # driving, transit, walking
        "language": "zh-TW",
        "key": API_KEY
    }
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                return element['distance']['text'], element['duration']['text']
            return "位置不明", "無法計算"
    except:
        return "連線失敗", "請檢查網路"
    return "計算中", "請稍候"

# --- 載入與處理資料庫 ---
@st.cache_data
def load_data():
    try:
        # 讀取你的檔案
        df = pd.read_csv('Scenic_Spot_C_f.csv')
        
        # 【核心修正】自動偵測欄位名稱，避免 KeyError: '縣市'
        # 這裡會檢查 CSV 裡有沒有長得像「縣市」或「City」的欄位
        possible_city_cols = ['縣市', '縣市別', 'City', 'city', '縣市名稱']
        target_col = None
        for col in possible_city_cols:
            if col in df.columns:
                target_col = col
                break
        
        if target_col and target_col != '縣市':
            df = df.rename(columns={target_col: '縣市'})
            
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
    # 優化：天數開放至 7 天
    days = st.slider("預計旅遊天數", 1, 7, 3)
    
    # 這裡的選項建議與你的 CSV 內容一致
    city_options = ["宜蘭縣", "南投縣", "臺北市", "臺中市", "高雄市", "花蓮縣", "桃園市"]
    city = st.selectbox("選擇目的縣市", city_options)
    
    # 優化：真實交通工具選擇
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    # 優化：住宿地址作為起點與終點
    stay_addr = st.text_input("輸入當晚住宿/起點地址", "宜蘭火車站")

# --- 核心邏輯：生成排程 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        # 篩選縣市景點
        if '縣市' not in df.columns:
            st.error(f"❌ 資料庫中找不到縣市欄位。目前的欄位有：{df.columns.tolist()}")
        else:
            filtered_df = df[df['縣市'].str.contains(city, na=False)]
            
            if filtered_df.empty:
                st.warning(f"目前資料庫中找不到包含「{city}」的景點。")
            else:
                st.header(f"📍 為您規劃的 {city} {days} 日遊")
                st.caption(f"🏠 每日起點/終點：{stay_addr} | 🚗 交通工具：{transport_mode}")

                for day in range(1, days + 1):
                    with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                        # 隨機抽取 3 個景點
                        sample_count = min(len(filtered_df), 3)
                        daily_spots = filtered_df.sample(sample_count)['景點名稱'].tolist()
                        
                        current_origin = stay_addr
                        
                        for i, spot in enumerate(daily_spots):
                            # 呼叫 Google API 獲取真實路網數據
                            dist, travel_time = get_google_travel_info(current_origin, spot, transport_mode)
                            
                            st.markdown(f"#### 第 {i+1} 站：{spot}")
                            st.write(f"⏱️ **交通預估**：從上一站移動約 **{dist}** (預計耗時 **{travel_time}**)")
                            st.markdown("---")
                            current_origin = spot
                        
                        # 回程計算
                        dist_back, time_back = get_google_travel_info(current_origin, stay_addr, transport_mode)
                        st.success(f"🌙 行程結束：返回住宿點 **{stay_addr}** (約需 {time_back})")
    else:
        st.error("請確認 Scenic_Spot_C_f.csv 已上傳。")
