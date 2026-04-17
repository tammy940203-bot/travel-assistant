import streamlit as st
import pandas as pd
import requests
import random

# 1. API 金鑰
if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 請設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

# 2. 地理資訊計算
def get_google_travel_info(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "language": "zh-TW", "key": API_KEY}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
        return "計算中", "約 15-25 分鐘"
    except:
        return "連線中", "稍後更新"

@st.cache_data
def load_data():
    try:
        return pd.read_csv('Scenic_Spot_C_f.csv')
    except:
        return None

df = load_data()

if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None

st.set_page_config(page_title="全台智能旅遊助手 V5.4", layout="wide")
st.title("全台智能旅遊助手 V5.4 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 2)
    city_options = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "宜蘭縣", "花蓮縣"]
    city = st.selectbox("選擇目的縣市", city_options)
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_pt = st.text_input("🚩 起點", "臺北車站")
    hotel_pt = st.text_input("🏨 住宿", "飯店/車站")

# --- 核心邏輯 ---
if st.button("🚀 啟動 AI 智能路徑優化"):
    if df is not None:
        city_alt = city.replace("臺", "台")
        # 1. 抓取該縣市所有資料
        filtered_df = df[df['Add'].str.contains(f"{city}|{city_alt}", na=False)]
        
        # 2. 終極黑名單 (加入「世代、室、閱、讀」等隱藏書店關鍵字)
        bad_words = ['書', '閱', '讀', '世代', '室', '藥局', '診所', '服務處', '辦公室', '補習班', '協會']
        clean_df = filtered_df[~filtered_df['Name'].str.contains('|'.join(bad_words), na=False)].copy()
        
        # 3. 檢查點夠不夠 (3個點 * 天數)
        total_needed = days * 3
        if len(clean_df) < total_needed:
            st.error(f"⚠️ {city} 剩餘觀光景點不足 (僅剩 {len(clean_df)} 個)，請減少天數或換個城市試試！")
        else:
            # 4. 一次性抽取所有天數需要的「不重複」景點
            all_selected_spots = clean_df.sample(n=total_needed).to_dict('records')
            
            final_itinerary = []
            spot_idx = 0
            
            for d in range(1, days + 1):
                day_spots_data = []
                current_origin = start_pt if d == 1 else hotel_pt
                
                # 每一天分配 3 個不重複的點
                for _ in range(3):
                    row = all_selected_spots[spot_idx]
                    search_dest = f"{city}{row['Name']}"
                    dist, dur = get_google_travel_info(current_origin, search_dest, transport_mode)
                    
                    day_spots_data.append({
                        "name": row['Name'],
                        "from": current_origin,
                        "dist": dist,
                        "dur": dur
                    })
                    current_origin = search_dest
                    spot_idx += 1
                
                _, back_dur = get_google_travel_info(current_origin, hotel_pt, transport_mode)
                final_itinerary.append({"day": d, "spots": day_spots_data, "back": back_dur})
            
            st.session_state.current_plan = final_itinerary

# --- 渲染 ---
if st.session_state.current_plan:
    for day_data in st.session_state.current_plan:
        with st.expander(f"📅 第 {day_data['day']} 天", expanded=True):
            for i, s in enumerate(day_data['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.info(f"🚗 從 **{s['from']}** 到 **{s['name']}** | 耗時：{s['dur']}")
            st.warning(f"🌙 返回 **{hotel_pt}** (耗時：{day_data['back']})")
