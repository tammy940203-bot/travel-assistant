import streamlit as st
import pandas as pd
import requests
import random

# 1. 從 Secrets 安全讀取金鑰 (請確保 Secrets 裡面有名稱叫 MAPS_API_KEY 的標籤)
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Cloud 的 Secrets 中設定 MAPS_API_KEY")
    st.stop()

# 2. 定義 Google Maps 距離矩陣函式 (解決交通時間不準的問題)
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
            else:
                return "未知距離", "無法計算 (請檢查地點名稱)"
    except Exception as e:
        return "連線錯誤", "請稍後再試"
    return "計算中", "請稍候"

# --- 載入資料庫 ---
@st.cache_data
def load_data():
    # 請確保你的 CSV 檔案名稱與 GitHub 上的檔案名稱完全一致
    try:
        df = pd.read_csv('Scenic_Spot_C_f.csv')
        return df
    except:
        st.error("❌ 找不到景點資料庫 CSV 檔案，請確認檔案已上傳至 GitHub")
        return None

df = load_data()

# --- UI 介面設定 ---
st.set_page_config(page_title="智能旅遊助手 V3.0", layout="wide")
st.title("全台智能旅遊助手 V3.0 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    # 優化 1：天數開放至 7 天
    days = st.slider("預計旅遊天數", 1, 7, 3)
    
    # 這裡的選項建議與你的 CSV '縣市' 欄位名稱一致
    city_options = ["宜蘭縣", "南投縣", "臺北市", "臺中市", "高雄市", "花蓮縣"]
    city = st.selectbox("選擇目的縣市", city_options)
    
    # 優化 2：提供多樣交通工具
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    # 優化 3：加入住宿地址作為行程錨點
    stay_addr = st.text_input("輸入當晚住宿/起點地址", "宜蘭火車站")

# --- 核心邏輯：生成排程 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        # 篩選該縣市的景點
        filtered_df = df[df['縣市'] == city]
        
        if filtered_df.empty:
            st.warning(f"目前資料庫中找不到 {city} 的景點，請檢查縣市名稱是否完全正確。")
        else:
            st.header(f"📍 為您規劃的 {city} {days} 日遊")
            st.caption(f"🏠 每日起點/終點：{stay_addr} | 🚗 交通工具：{transport_mode}")

            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    # 隨機抽取 3 個景點 (解決行程稀疏問題)
                    sample_size = min(len(filtered_df), 3)
                    daily_spots = filtered_df.sample(sample_size)['景點名稱'].tolist()
                    
                    current_origin = stay_addr # 每天的第一站從住宿點出發
                    
                    for i, spot in enumerate(daily_spots):
                        # 呼叫 Google API 算真實數據
                        dist, travel_time = get_google_travel_info(current_origin, spot, transport_mode)
                        
                        st.markdown(f"#### 第 {i+1} 站：{spot}")
                        st.write(f"⏱️ **交通預估**：從上一站移動約 **{dist}** (預計耗時 **{travel_time}**)")
                        st.markdown("---")
                        
                        current_origin = spot # 更新下一站的起點
                    
                    # 每天最後一站算回住宿點的時間
                    dist_back, time_back = get_google_travel_info(current_origin, stay_addr, transport_mode)
                    st.success(f"🌙 行程結束：返回住宿點 **{stay_addr}** (約需 {time_back})")
    else:
        st.error("無法執行，因為資料庫載入失敗。")
