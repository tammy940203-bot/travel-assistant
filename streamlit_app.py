import streamlit as st
import pandas as pd
import requests
import random

# 1. 從 Secrets 安全讀取金鑰
API_KEY = st.secrets["MAPS_API_KEY"]

# 2. 定義 Google Maps 距離矩陣函式 (解決交通方式太爛的問題)
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
    except:
        pass
    return "計算中", "請稍候"

# --- UI 介面設定 ---
st.title("全台智能旅遊助手 V3.0 🌍")

with st.sidebar:
    st.header("行程設定")
    # 解決缺點 2：將天數上限調整至 7 天
    days = st.slider("預計旅遊天數", 1, 7, 3)
    
    city = st.selectbox("選擇目的縣市", ["宜蘭縣", "南投縣", "台北市", "台中市"]) # 可依你的 CSV 調整
    
    # 解決缺點 1：提供更多樣的交通工具選擇
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    # 解決缺點 3：新增住宿地址欄位
    stay_addr = st.text_input("輸入當晚住宿地址 (例如：宜蘭火車站)", "宜蘭火車站")

# --- 核心邏輯：生成豐富行程 ---
if st.button("開始自動排程"):
    # 讀取你的景點資料庫 (請確保檔名正確)
    # df = pd.read_csv('Scenic_Spot_C_f.csv') 
    
    st.header(f"📍 為您規劃的 {city} {days} 日遊")
    st.caption(f"🏠 每日起點/終點：{stay_addr}")

    # 模擬從資料庫抽取的逻辑 (這裡改為每天安排 3 站，解決只有 3 站能跑的問題)
    for day in range(1, days + 1):
        with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
            # 這裡示範每天挑選 3 個點，你可以改為從 df 篩選
            daily_spots = [f"景點 A-{day}", f"景點 B-{day}", f"景點 C-{day}"] 
            
            current_origin = stay_addr # 每天的第一站從住宿點出發
            
            for i, spot in enumerate(daily_spots):
                # 呼叫 Google API 計算真實交通時間
                dist, travel_time = get_google_travel_info(current_origin, spot, transport_mode)
                
                st.write(f"**第 {i+1} 站：{spot}**")
                st.caption(f"➡️ 從上一站移動：約 {dist} (預估耗時 {travel_time})")
                st.markdown("---")
                
                current_origin = spot # 更新下一站的起點
            
            # 每天最後一站算回住宿點的時間
            dist_back, time_back = get_google_travel_info(current_origin, stay_addr, transport_mode)
            st.success(f"🌙 行程結束：返回住宿點 {stay_addr} (約 {time_back})")
