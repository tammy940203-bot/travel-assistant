import streamlit as st
import pandas as pd
import requests

# 1. API 金鑰讀取
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！")
    st.stop()

# 2. 取得距離與時間 (回傳秒數與公里數方便計算)
def get_travel_data(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "key": API_KEY, "language": "zh-TW"}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                return {
                    "dist_txt": element['distance']['text'],
                    "dur_txt": element['duration']['text'],
                    "dur_sec": element['duration']['value'] # 秒數
                }
    return None

# --- UI 與資料載入 ---
st.set_page_config(page_title="智能旅遊助手 V4.0", layout="wide")
st.title("全台智能旅遊助手 V4.0 (順路優化版) 🌍")

df = pd.read_csv('Scenic_Spot_C_f.csv')

with st.sidebar:
    st.header("⚙️ 行程設定")
    city = st.selectbox("選擇目的縣市", ["臺北市", "宜蘭縣", "桃園市", "臺中市", "高雄市"]) # 依此類推
    transport_mode = st.radio("交通方式", ["driving", "transit"])
    start_point = st.text_input("🚩 設定出發起點", "宜蘭火車站")
    hotel_addr = st.text_input("🏨 設定住宿點", "宜蘭某某飯店")
    max_travel_limit = 180 * 60 # 3小時轉秒數

# --- 核心邏輯：最近鄰搜尋 ---
if st.button("🚀 生成順路優化行程"):
    filtered_df = df[df['Add'].str.contains(city, na=False)].copy()
    
    for day in range(1, 4): # 以3日遊為例
        with st.expander(f"📅 第 {day} 天順路行程", expanded=True):
            current_loc = start_point if day == 1 else hotel_addr
            total_dur_sec = 0
            daily_itinerary = []
            
            # 嘗試找 3 個點
            for _ in range(3):
                # 為了效率，先隨機取10個點來計算距離(避免全台灣掃描太慢)
                candidates = filtered_df.sample(min(10, len(filtered_df)))
                best_spot = None
                min_dur = float('inf')
                
                for _, row in candidates.iterrows():
                    data = get_travel_data(current_loc, f"{city}{row['Name']}", transport_mode)
                    if data and data['dur_sec'] < min_dur:
                        # 檢查加入這站後會不會爆 3 小時
                        if total_dur_sec + data['dur_sec'] <= max_travel_limit:
                            min_dur = data['dur_sec']
                            best_spot = {**row, **data}
                
                if best_spot:
                    daily_itinerary.append(best_spot)
                    total_dur_sec += best_spot['dur_sec']
                    current_loc = best_spot['Name']
                    # 移除已選景點避免重複
                    filtered_df = filtered_df[filtered_df['Name'] != best_spot['Name']]

            # 最後回飯店的時間也要算進去
            back_data = get_travel_data(current_loc, hotel_addr, transport_mode)
            
            # 顯示結果
            for i, s in enumerate(daily_itinerary):
                st.markdown(f"**第 {i+1} 站：{s['Name']}**")
                st.caption(f"🏁 從前一站出發：{s['dist_txt']} (耗時 {s['dur_txt']})")
            
            if back_data:
                total_dur_sec += back_data['dur_sec']
                st.success(f"🌙 今日總交通時間：{total_dur_sec // 60} 分鐘 (限制 180 分鐘內)")
