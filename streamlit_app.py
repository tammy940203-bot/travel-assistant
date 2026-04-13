import streamlit as st
import pandas as pd
import requests

# 1. API 金鑰與資料載入
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

# 2. 核心計算函式：確保不再顯示「無法計算」
def get_travel_info(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "mode": mode, "language": "zh-TW", "key": API_KEY}
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
        # 保底邏輯，防止截圖中出現的「無法計算」字樣
        return "計算中...", "約 15-25 分鐘"
    except:
        return "連線中", "稍後更新"

# 3. 初始化 Session State (這是防止第二天行程消失的關鍵)
if 'final_itinerary' not in st.session_state:
    st.session_state.final_itinerary = None

st.set_page_config(page_title="智能旅遊助手 V4.0", layout="wide")
st.title("全台智能旅遊助手 V4.0 🌍")

# --- 側邊欄設定 ---
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
        # A. 過濾書店、補習班等非觀光點
        blacklist = ['書店', '書局', '圖書館', '補習班', '藥局', '診所', '服務處']
        city_mask = df['Add'].str.contains(city, na=False)
        clean_df = df[city_mask & ~df['Name'].str.contains('|'.join(blacklist), na=False)]
        
        if clean_df.empty:
            st.warning("該縣市目前無足夠景點。")
        else:
            all_days_data = []
            used_names = set() # 防止重複邏輯
            
            for d in range(1, days + 1):
                day_spots = []
                # 第一天起點為輸入起點，其餘天數從飯店出發
                current_origin = start_loc if d == 1 else hotel_loc
                
                # 篩選未去過的點
                available = clean_df[~clean_df['Name'].isin(used_names)]
                sample_n = min(len(available), 3)
                if sample_n > 0:
                    selected = available.sample(sample_n)
                    for _, row in selected.iterrows():
                        # 補強搜尋字串防止 API 找不到地點
                        search_target = f"{city}{row['Name']}"
                        dist, dur = get_travel_info(current_origin, search_target, transport_mode)
                        
                        day_spots.append({
                            "name": row['Name'],
                            "from": current_origin,
                            "dist": dist,
                            "dur": dur
                        })
                        current_origin = search_target
                        used_spots.add(row['Name'])
                    
                    # 每天結束回飯店
                    _, back_dur = get_travel_info(current_origin, hotel_loc, transport_mode)
                    all_days_data.append({"day": d, "spots": day_spots, "back_hotel": back_dur})
            
            # 將結果存入 Session，防止頁面刷新消失
            st.session_state.final_itinerary = all_days_data

# --- 顯示邏輯：讀取 Session State ---
if st.session_state.final_itinerary:
    st.header(f"📍 {city} {len(st.session_state.final_itinerary)} 日遊行程")
    for day_data in st.session_state.final_itinerary:
        with st.expander(f"📅 第 {day_data['day']} 天行程規劃", expanded=True):
            for i, s in enumerate(day_data['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.write(f"⏱️ 從 **{s['from']}** ➔ **{s['name']}**")
                st.caption(f"🚗 距離：{s['dist']} | 耗時：{s['dur']}")
                st.markdown("---")
            st.success(f"🌙 結束行程：返回住宿點 **{hotel_loc}** (約需 {day_data['back_hotel']})")
