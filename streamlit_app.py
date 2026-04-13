import streamlit as st
import pandas as pd
import requests

# 1. 安全金鑰設定
if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

def get_travel_data(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "language": "zh-TW", "key": API_KEY}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                return {"dist_txt": element['distance']['text'], "dur_txt": element['duration']['text'], "dur_sec": element['duration']['value']}
    except: pass
    return None

@st.cache_data
def load_data():
    try:
        return pd.read_csv('Scenic_Spot_C_f.csv')
    except:
        return None

df = load_data()

st.set_page_config(page_title="智能旅遊助手 V4.8", layout="wide")
st.title("全台智能旅遊助手 V4.8 (最終穩定版) 🌍")

# 初始化 Session State，這步最重要！
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["臺北市", "宜蘭縣", "新北市", "桃園市", "臺中市", "高雄市", "花蓮縣"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_point = st.text_input("🚩 第一天起點", "臺北車站")
    hotel_addr = st.text_input("🏨 住宿/終點名稱", "台北市飯店")

# --- 生成邏輯 ---
if st.button("🚀 重新生成完整行程"):
    if df is not None:
        exclude = ['書局', '書店', '圖書館', '補習班', '藥局', '診所', '服務處']
        main_df = df[df['Add'].str.contains(city, na=False)].copy()
        main_df = main_df[~main_df['Name'].str.contains('|'.join(exclude), na=False)]
        
        all_days_data = []
        used_names = []

        for day in range(1, days + 1):
            day_spots = []
            current_loc = start_point if day == 1 else hotel_addr
            day_total_sec = 0
            
            for i in range(3):
                available_df = main_df[~main_df['Name'].isin(used_names)]
                if available_df.empty: break
                
                # 廣域抽樣 40 個點
                candidates = available_df.sample(min(40, len(available_df)))
                selected_spot = None
                
                # 優先找單趟 45 分鐘內的點
                for idx, row in candidates.iterrows():
                    data = get_travel_data(current_loc, f"{city}{row['Name']}", transport_mode)
                    if data and data['dur_sec'] < 2700:
                        selected_spot = row.to_dict()
                        selected_spot['travel'] = data
                        break
                
                # 如果找不到順路的，強行隨機塞一個
                if not selected_spot:
                    lucky_row = candidates.iloc[0]
                    data = get_travel_data(current_loc, f"{city}{lucky_row['Name']}", transport_mode)
                    if not data: data = {"dist_txt": "計算中", "dur_txt": "20 分鐘", "dur_sec": 1200}
                    selected_spot = lucky_row.to_dict()
                    selected_spot['travel'] = data

                if selected_spot:
                    day_spots.append(selected_spot)
                    used_names.append(selected_spot['Name'])
                    day_total_sec += selected_spot['travel']['dur_sec']
                    current_loc = f"{city}{selected_spot['Name']}"

            all_days_data.append({"day": day, "spots": day_spots, "total_sec": day_total_sec})
        
        st.session_state.itinerary = all_days_data

# --- 顯示邏輯 (與計算分開，避免刷新消失) ---
if st.session_state.itinerary:
    for day_info in st.session_state.itinerary:
        with st.expander(f"📅 第 {day_info['day']} 天行程規劃", expanded=True):
            if not day_info['spots']:
                st.write("這天沒有排到行程...")
            else:
                for idx, s in enumerate(day_info['spots']):
                    st.markdown(f"### 第 {idx+1} 站：{s['Name']}")
                    if pd.notna(s.get('Picture1')):
                        st.image(s['Picture1'], use_container_width=True)
                    
                    desc = str(s.get('Description', ''))
                    if len(desc) < 10 or desc == 'nan':
                        desc = f"這是位於{city}的精選旅遊點，非常值得一遊。"
                    st.write(f"📖 **景點特色**：{desc[:100]}...")
                    st.caption(f"🚗 交通：{s['travel']['dist_txt']} (約 {s['travel']['dur_txt']})")
                    st.markdown("---")
            st.success(f"🌙 今日累計交通耗時：{day_info['total_sec'] // 60} 分鐘")
