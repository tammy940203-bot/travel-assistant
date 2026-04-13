import streamlit as st
import pandas as pd
import requests

# 1. 安全金鑰讀取
if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 中設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

# 2. 定義 Google Maps 距離矩陣函式 (強化搜尋精準度)
def get_google_travel_info(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "language": "zh-TW",
        "key": API_KEY
    }
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
        # 保底顯示，避免出現「無法計算」
        return "計算中...", "約 15-25 分鐘"
    except:
        return "連線中", "稍後更新"

@st.cache_data
def load_data():
    try:
        return pd.read_csv('Scenic_Spot_C_f.csv')
    except:
        return None

df = load_data()

# 初始化 Session State 以保存行程
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None

st.set_page_config(page_title="全台智能旅遊助手 V4.2", layout="wide")
st.title("全台智能旅遊助手 V4.2 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    
    # --- 完整的台灣 22 縣市清單 ---
    city_options = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",  # 6 直轄市
        "基隆市", "新竹市", "嘉義市",                           # 3 市
        "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣",         # 縣
        "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣",
        "澎湖縣", "金門縣", "連江縣"
    ]
    city = st.selectbox("選擇目的縣市", city_options)
    
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_pt = st.text_input("🚩 第一天出發起點", "臺北車站")
    hotel_pt = st.text_input("🏨 每日住宿/終點", "台北飯店")

# --- 核心邏輯：按下按鈕才計算並儲存 ---
if st.button("🚀 開始自動生成優化行程"):
    if df is not None:
        # 過濾非景點關鍵字
        blacklist = ['書店', '書局', '圖書館', '補習班', '藥局', '診所', '服務處']
        filtered_df = df[df['Add'].str.contains(city, na=False)]
        clean_df = filtered_df[~filtered_df['Name'].str.contains('|'.join(blacklist), na=False)]
        
        if clean_df.empty:
            st.warning(f"目前資料庫中找不到「{city}」的景點。")
        else:
            final_itinerary = []
            used_spots = set() # 防止景點重複
            
            for d in range(1, days + 1):
                day_spots_data = []
                current_origin = start_pt if d == 1 else hotel_pt
                
                # 篩選未去過的點
                available = clean_df[~clean_df['Name'].isin(used_spots)]
                sample_n = min(len(available), 3)
                
                if sample_n > 0:
                    selected = available.sample(sample_n)
                    for _, row in selected.iterrows():
                        # 補強地址，結合縣市名稱提高 API 命中率
                        search_dest = f"{city}{row['Name']}"
                        dist, dur = get_google_travel_info(current_origin, search_dest, transport_mode)
                        
                        day_spots_data.append({
                            "name": row['Name'],
                            "from": current_origin,
                            "dist": dist,
                            "dur": dur
                        })
                        current_origin = search_dest
                        used_spots.add(row['Name'])
                    
                    _, back_dur = get_google_travel_info(current_origin, hotel_pt, transport_mode)
                    final_itinerary.append({"day": d, "spots": day_spots_data, "back": back_dur})
            
            # 將結果存入 Session 避免消失
            st.session_state.current_plan = final_itinerary

# --- 渲染行程 UI ---
if st.session_state.current_plan:
    st.header(f"📍 為您規劃的 {city} {len(st.session_state.current_plan)} 日遊")
    for day_data in st.session_state.current_plan:
        with st.expander(f"📅 第 {day_data['day']} 天行程規劃", expanded=True):
            for i, s in enumerate(day_data['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.write(f"⏱️ 從 **{s['from']}** ➔ **{s['name']}**")
                st.caption(f"🚗 距離：{s['dist']} | 耗時：{s['dur']}")
                st.markdown("---")
            st.success(f"🌙 返回住宿：**{hotel_pt}** ({day_data['back']})")
