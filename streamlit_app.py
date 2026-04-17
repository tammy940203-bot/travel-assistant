import streamlit as st
import pandas as pd
import requests
import random

# --- 1. 初始化與安全金鑰 ---
st.set_page_config(page_title="全台智能旅遊助手", layout="wide")

# 建議將 API Key 放在 Streamlit Secrets 中
if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 中設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

# --- 2. 工具函式：計算路徑與載入資料 ---
def get_travel_info(origin, destination, mode_str):
    """串接 Google Maps API 計算真實耗時"""
    mode = "driving" if mode_str == "自行開車" else "transit"
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin, "destinations": destination,
        "mode": mode, "language": "zh-TW", "key": API_KEY
    }
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
    
    taiwan_cities = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", 
        "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", 
        "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    
    def extract_standard_city(address):
        address = str(address)
        for city in taiwan_cities:
            if city in address or city.replace("臺", "台") in address:
                return city
        return None

    df['City'] = df['Add'].apply(extract_standard_city)
    df = df.dropna(subset=['City'])
    
    # 額外過濾：移除明顯不是景點的地點 (例如書店、辦公室)
    blacklist = ['藥局', '診所', '補習班', '辦公室', '服務處']
    df = df[~df['Name'].str.contains('|'.join(blacklist), na=False)]
    
    return df, taiwan_cities

# --- 3. 介面與資料處理 ---
df, city_list = load_data()
available_cities = sorted([c for c in city_list if c in df['City'].unique()])

if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

st.title("全台智能旅遊助手 🌍")
st.markdown("---")

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
    
    total_spots_needed = days * 3 # 每天排 3 個景點
    if len(city_df) < total_spots_needed:
        st.warning(f"目前 {city} 景點資料較少，建議減少天數。")
        total_spots_needed = len(city_df)
    
    # 【關鍵優化】：一次性抽取「全行程不重複」的景點
    selected_spots = city_df.sample(n=total_spots_needed).to_dict('records')
    
    full_plan = []
    spot_idx = 0
    
    for d in range(1, days + 1):
        day_data = []
        # 決定當天出發點 (第一天用自填，之後用飯店)
        current_loc = start_pt if d == 1 else hotel_pt
        
        # 每天取 3 個點 (如果還夠的話)
        for _ in range(3):
            if spot_idx < len(selected_spots):
                spot = selected_spots[spot_idx]
                # 結合縣市名讓 API 搜尋更精準
                search_dest = f"{city}{spot['Name']}"
                dist, dur = get_travel_info(current_loc, search_dest, transport)
                
                day_data.append({
                    "name": spot['Name'],
                    "addr": spot['Add'],
                    "dist": dist,
                    "dur": dur,
                    "from": current_loc
                })
                current_loc = search_dest
                spot_idx += 1
        
        # 計算回飯店的時間
        _, back_dur = get_travel_info(current_loc, hotel_pt, transport)
        full_plan.append({"day": d, "spots": day_data, "back": back_dur})
    
    st.session_state.itinerary = full_plan

# --- 5. 渲染行程結果 ---
if st.session_state.itinerary:
    st.subheader(f"📅 為您規劃的 {city} {len(st.session_state.itinerary)} 日遊行程")
    
    for day in st.session_state.itinerary:
        with st.expander(f"第 {day['day']} 天 行程明細", expanded=True):
            for i, s in enumerate(day['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.write(f"📍 地址：{s['addr']}")
                st.caption(f"⏱️ 移動：從 **{s['from']}** 前往，約需 **{s['dur']}** ({s['dist']})")
                st.markdown("---")
            st.success(f"🌙 結束行程，返回 **{hotel_pt}** (交通預估：{day['back']})")
    
    st.info("💡 此行程已整合 Google Maps 實時路徑模型。")
