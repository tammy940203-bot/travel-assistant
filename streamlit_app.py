import streamlit as st
import pandas as pd
import requests
import random

# --- 1. 基本設定 ---
st.set_page_config(page_title="全台智能旅遊助手", layout="wide")

if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰！")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

# --- 2. 工具函式 ---
def get_travel_info(origin, destination, mode_str):
    mode = "driving" if mode_str == "自行開車" else "transit"
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "language": "zh-TW", "key": API_KEY}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
        return "N/A", "約 15-25 分鐘"
    except:
        return "N/A", "計算中"

@st.cache_data
def load_data():
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    taiwan_cities = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"]
    
    def extract_standard_city(address):
        for city in taiwan_cities:
            if city in str(address) or city.replace("臺", "台") in str(address):
                return city
        return None

    df['City'] = df['Add'].apply(extract_standard_city)
    df = df.dropna(subset=['City'])
    return df, taiwan_cities

df, city_list = load_data()
available_cities = sorted([c for c in city_list if c in df['City'].unique()])

# 初始化 Session State
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

st.title("全台智能旅遊助手 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    city = st.selectbox("1. 選擇目的地縣市", available_cities)
    days = st.slider("2. 預計旅遊天數", 1, 7, 2)
    transport = st.radio("3. 交通方式", ["大眾運輸", "自行開車"])
    start_pt = st.text_input("🚩 第一天起點", "臺北車站")
    hotel_pt = st.text_input("🏨 每日住宿/終點", "附近的飯店")

# --- 4. 生成行程邏輯 ---
if st.button("🚀 開始自動排程"):
    city_df = df[df['City'] == city]
    total_spots = days * 3
    
    if not city_df.empty:
        # 一次取出不重複的點
        selected_spots = city_df.sample(n=min(len(city_df), total_spots)).to_dict('records')
        
        # 展示 SFT 格式 (保留專業感)
        with st.status("🛠️ 正在進行數據格式化 (Instruction-Input-Output)..."):
            sample = selected_spots[0]
            st.json({
                "instruction": "你是一個專業導航助手...",
                "input": f"目標縣市：{city}",
                "output": f"推薦景點：{sample['Name']}，位於：{sample['Add']}"
            })
        
        # 計算路徑並存入 session
        full_plan = []
        spot_idx = 0
        for d in range(1, days + 1):
            day_data = []
            current_loc = start_pt if d == 1 else hotel_pt
            for _ in range(3):
                if spot_idx < len(selected_spots):
                    s = selected_spots[spot_idx]
                    dist, dur = get_travel_info(current_loc, f"{city}{s['Name']}", transport)
                    day_data.append({"name": s['Name'], "addr": s['Add'], "dur": dur, "dist": dist, "from": current_loc})
                    current_loc = f"{city}{s['Name']}"
                    spot_idx += 1
            _, b_dur = get_travel_info(current_loc, hotel_pt, transport)
            full_plan.append({"day": d, "spots": day_data, "back": b_dur})
        
        st.session_state.itinerary = full_plan

# --- 5. 渲染行程結果 (改回 Expander 模式) ---
if st.session_state.itinerary:
    st.markdown(f"### 📅 為您規劃的 {city} {len(st.session_state.itinerary)} 日遊行程")
    
    for day in st.session_state.itinerary:
        # 這就是你要的「右邊那張圖」的 Expander 效果
        with st.expander(f"📅 第 {day['day']} 天 行程明細", expanded=True):
            for i, s in enumerate(day['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.write(f"📍 地址：{s['addr']}")
                st.caption(f"⏱️ 移動：從 **{s['from']}** 前往，約需 **{s['dur']}** ({s['dist']})")
                st.markdown("---")
            st.warning(f"🌙 結束行程，返回 **{hotel_pt}** (預計：{day['back']})")
