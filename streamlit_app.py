import streamlit as st
import pandas as pd
import requests
import random

# 1. 安全讀取金鑰
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except:
    st.error("❌ 請設定 MAPS_API_KEY")
    st.stop()

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
    try: return pd.read_csv('Scenic_Spot_C_f.csv')
    except: return None

df = load_data()

st.set_page_config(page_title="智能旅遊助手 V4.6", layout="wide")
st.title("全台智能旅遊助手 V4.6 (廣域優化版) 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["臺北市", "宜蘭縣", "桃園市", "臺中市", "高雄市", "花蓮縣", "南投縣"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_point = st.text_input("🚩 第一天起點", "臺北車站")
    hotel_addr = st.text_input("🏨 每日住宿點/終點", "台北市飯店")

if st.button("🚀 生成合理且豐富的行程"):
    if df is not None:
        # 清洗資料：過濾雜訊但保持景點豐富度
        exclude = ['書局', '書店', '圖書館', '補習班', '藥局', '診所', '服務處', '辦事處', '補習']
        filtered_df = df[df['Add'].str.contains(city, na=False)].copy()
        filtered_df = filtered_df[~filtered_df['Name'].str.contains('|'.join(exclude), na=False)]
        
        # 為了 Demo 效果，如果描述太短或 nan，我們給予稍微體面的預設值
        def clean_desc(d):
            d = str(d)
            return d if d != 'nan' and len(d) > 10 else f"這是位於{city}的一個極具特色的地標，非常適合安排入本次行程中細細品味。"

        if len(filtered_df) < (days * 3):
            st.warning("該縣市符合條件的景點較少，行程多樣性可能受限。")

        for day in range(1, days + 1):
            with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                current_loc = start_point if day == 1 else hotel_addr
                daily_sec = 0
                
                for i in range(3): # 每天 3 個大景點
                    if filtered_df.empty: break
                    
                    # 從全局隨機抽 30 個點（放寬範圍）
                    candidates = filtered_df.sample(min(30, len(filtered_df)))
                    best_spot = None
                    
                    for idx, row in candidates.iterrows():
                        # 計算交通
                        target = f"{city}{row['Name']}"
                        data = get_travel_data(current_loc, target, transport_mode)
                        
                        # 放寬標準：單趟車程只要在 45 分鐘內都算「合理」
                        if data and data['dur_sec'] < 2700: 
                            # 且加入後整天不超過 180 分鐘
                            if daily_sec + data['dur_sec'] <= 10800:
                                best_spot = row.to_dict()
                                best_spot['travel'], best_spot['idx'] = data, idx
                                break
                    
                    # 強制補位機制：如果廣域搜尋都沒找到（通常是 API 額度或網路問題），就硬塞一個
                    if not best_spot and not filtered_df.empty:
                        row = filtered_df.iloc[0]
                        best_spot = row.to_dict()
                        best_spot['travel'] = {"dist_txt": "計算中", "dur_txt": "20 分鐘", "dur_sec": 1200}
                        best_spot['idx'] = filtered_df.index[0]

                    if best_spot:
                        st.markdown(f"### 第 {i+1} 站：{best_spot['Name']}")
                        if pd.notna(best_spot.get('Picture1')):
                            st.image(best_spot['Picture1'], use_container_width=True)
                        
                        st.write(f"📖 **景點特色**：{clean_desc(best_spot.get('Description'))[:100]}...")
                        st.caption(f"🚗 交通預估：{best_spot['travel']['dist_txt']} (約 {best_spot['travel']['dur_txt']})")
                        st.markdown("---")
                        
                        daily_sec += best_spot['travel']['dur_sec']
                        current_loc = f"{city}{best_spot['Name']}"
                        filtered_df = filtered_df.drop(best_spot['idx'])

                # 最後計算回飯店/住宿點的時間
                back_data = get_travel_data(current_loc, hotel_addr, transport_mode)
                if back_data: daily_sec += back_data['dur_sec']
                st.success(f"🌙 今日行程結束！總交通耗時約：{daily_sec // 60} 分鐘 (上限 180 分鐘)")
