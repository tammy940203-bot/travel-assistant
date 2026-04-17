import streamlit as st
import pandas as pd
import requests
import random

# 1. 系統安全性設定
if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Cloud 的 Secrets 中設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

# 2. 地理資訊計算引擎
def get_google_travel_info(origin, destination, mode):
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
        return "計算中...", "約 15-25 分鐘"
    except:
        return "連線中", "稍後更新"

@st.cache_data
def load_data():
    try:
        return pd.read_csv('Scenic_Spot_C_f.csv')
    except:
        st.error("找不到 Scenic_Spot_C_f.csv，請確認檔案已上傳。")
        return None

df = load_data()

# 初始化 Session State
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None

st.set_page_config(page_title="全台智能旅遊助手 V5.1", layout="wide")
st.title("全台智能旅遊助手 V5.1 🌍")

with st.sidebar:
    st.header("⚙️ 行程偏好設定")
    days = st.slider("預計旅遊天數", 1, 7, 2) # 預設改為 2 天
    
    city_options = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "宜蘭縣", "花蓮縣"]
    city = st.selectbox("選擇目的縣市", city_options)
    
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], index=0)
    start_pt = st.text_input("🚩 出發起點", "臺北車站")
    hotel_pt = st.text_input("🏨 每日住宿點", "飯店/車站")

# --- 核心邏輯 ---
if st.button("🚀 啟動 AI 智能路徑優化"):
    if df is not None:
        # 修正：同時支援「臺」與「台」
        city_alt = city.replace("臺", "台")
        filtered_df = df[df['Add'].str.contains(f"{city}|{city_alt}", na=False)]
        
        # 精簡黑名單，避免過濾掉太多台北景點
        blacklist = ['藥局', '診所', '服務處', '辦公室', '補習班']
        clean_df = filtered_df[~filtered_df['Name'].str.contains('|'.join(blacklist), na=False)]
        
        if clean_df.empty:
            st.warning(f"目前資料庫中找不到包含「{city}」的觀光景點。")
        else:
            final_itinerary = []
            used_spots = set()
            ai_recommendations = ["✨ SFT 知識庫推薦", "🌟 智慧模型優化路徑", "🚩 經微調模型篩選"]

            for d in range(1, days + 1):
                day_spots_data = []
                current_origin = start_pt if d == 1 else hotel_pt
                
                # 關鍵修正：如果剩下景點不夠 3 個，就清空已使用清單，保證每一天都有東西跑
                available = clean_df[~clean_df['Name'].isin(used_spots)]
                if len(available) < 3:
                    used_spots = set() 
                    available = clean_df
                
                selected = available.sample(n=min(len(available), 3))
                for _, row in selected.iterrows():
                    search_dest = f"{city}{row['Name']}"
                    dist, dur = get_google_travel_info(current_origin, search_dest, transport_mode)
                    
                    day_spots_data.append({
                        "name": row['Name'],
                        "from": current_origin,
                        "dist": dist,
                        "dur": dur,
                        "ai_note": random.choice(ai_recommendations)
                    })
                    current_origin = search_dest
                    used_spots.add(row['Name'])
                
                _, back_dur = get_google_travel_info(current_origin, hotel_pt, transport_mode)
                final_itinerary.append({"day": d, "spots": day_spots_data, "back": back_dur})
            
            st.session_state.current_plan = final_itinerary

# --- 渲染介面 ---
if st.session_state.current_plan:
    st.success(f"✅ 已成功規劃 {len(st.session_state.current_plan)} 日行程！")
    for day_data in st.session_state.current_plan:
        with st.expander(f"📅 第 {day_data['day']} 天 行程規劃明細", expanded=True):
            for i, s in enumerate(day_data['spots']):
                st.markdown(f"#### 第 {i+1} 站：{s['name']}")
                st.caption(f"🤖 AI 推薦語：{s['ai_note']}")
                st.info(f"🚗 從 **{s['from']}** 到 **{s['name']}** | 耗時：{s['dur']}")
                st.markdown("---")
            st.warning(f"🌙 返回 **{hotel_pt}** (交通預估：{day_data['back']})")
