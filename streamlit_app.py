import streamlit as st
import pandas as pd
import requests

# 1. 金鑰與資料初始化
if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 請在 Streamlit Secrets 設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

@st.cache_data
def load_data():
    try:
        return pd.read_csv('Scenic_Spot_C_f.csv')
    except:
        return None

df = load_data()

def get_travel_info(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "language": "zh-TW", "key": API_KEY}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
        return "計算中...", "約 15-25 分鐘"
    except:
        return "連線中", "稍後更新"

# 初始化 Session State 防止刷新消失
if 'final_itinerary' not in st.session_state:
    st.session_state.final_itinerary = None

st.set_page_config(page_title="智能旅遊助手 V4.1", layout="wide")
st.title("全台智能旅遊助手 V4.1 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "宜蘭縣", "花蓮縣"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_loc = st.text_input("🚩 第一天起點", "宜蘭火車站")
    hotel_loc = st.text_input("🏨 每日住宿/終點", "伯斯飯店")

# --- 按鈕觸發計算 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        blacklist = ['書店', '書局', '圖書館', '補習班', '藥局', '診所', '服務處']
        city_mask = df['Add'].str.contains(city, na=False)
        clean_df = df[city_mask & ~df['Name'].str.contains('|'.join(blacklist), na=False)]
        
        if clean_df.empty:
            st.warning("該縣市目前無足夠景點。")
        else:
            all_days_data = []
            
            # 【核心修正】在這裡定義 used_spots，就不會再報 NameError 了！
            used_spots = set() 
            
            for d in range(1, days + 1):
                day_spots = []
                current_origin = start_loc if d == 1 else hotel_loc
                
                # 排除已選景點
                available = clean_df[~clean_df['Name'].isin(used_spots)]
                sample_n = min(len(available), 3)
                
                if sample_n > 0:
                    selected = available.sample(sample_n)
                    for _, row in selected.iterrows():
                        search_target = f"{city}{row['Name']}"
                        dist, dur = get_travel_info(current_origin, search_target, transport_mode)
                        
                        day_spots.append({
                            "name": row['Name'],
                            "from": current_origin,
                            "dist": dist,
                            "dur": dur
                        })
                        current_origin = search_target
                        # 這裡使用剛剛定義好的 used_spots
                        used_spots.add(row['Name']) 
                    
                    _, back_dur = get_travel_info(current_origin, hotel_loc, transport_mode)
                    all_days_data.append({"day": d, "spots": day_spots, "back_hotel": back_dur})
            
            st.session_state.final_itinerary = all_days_data

# --- 顯示行程 ---
if st.session_state.final_itinerary:
    st.header(f"📍 {city} {len(st.session_state.final_itinerary)} 日遊行程")
    for day_data in st.session_state.final_itinerary:
        with st.expander(f"📅 第 {day_data['day']} 天行程規劃", expanded=True):
            for i, s in enumerate(day_data['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.write(f"⏱️ 從 **{s['from']}** ➔ **{s['name']}**")
                st.caption(f"🚗 距離：{s['dist']} | 耗時：{s['dur']}")
                st.markdown("---")
            st.success(f"🌙 結束行程：返回住宿點 **{hotel_loc}** ({day_data['back_hotel']})")
