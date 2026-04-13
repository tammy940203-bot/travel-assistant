import streamlit as st
import pandas as pd
import requests

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

st.set_page_config(page_title="智能旅遊助手 V4.5", layout="wide")
st.title("全台智能旅遊助手 V4.5 (保底強化版) 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["臺北市", "宜蘭縣", "桃園市", "臺中市", "高雄市", "花蓮縣", "南投縣"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_point = st.text_input("🚩 第一天起點", "臺北車站")
    hotel_addr = st.text_input("🏨 每日住宿點", "台北市飯店")

if st.button("🚀 生成強韌行程"):
    if df is not None:
        # 清洗資料：排除非觀光雜訊
        exclude = ['書局', '書店', '圖書館', '補習班', '藥局', '診所', '服務處', '辦事處']
        filtered_df = df[df['Add'].str.contains(city, na=False)].copy()
        filtered_df = filtered_df[~filtered_df['Name'].str.contains('|'.join(exclude), na=False)]
        
        if filtered_df.empty:
            st.warning("該縣市資料庫內容不足。")
        else:
            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    current_loc = start_point if day == 1 else hotel_addr
                    daily_sec = 0
                    spots_found = 0
                    
                    # 嘗試抓 3 個點
                    for i in range(3):
                        if filtered_df.empty: break
                        
                        # 搜尋策略：先找 15 分鐘車程內的，找不到就隨機補位
                        candidates = filtered_df.sample(min(20, len(filtered_df)))
                        best_spot = None
                        
                        for idx, row in candidates.iterrows():
                            data = get_travel_data(current_loc, f"{city}{row['Name']}", transport_mode)
                            if data and data['dur_sec'] < 3600: # 1小時內車程
                                best_spot = row.to_dict()
                                best_spot['travel'], best_spot['idx'] = data, idx
                                break 

                        # 【保底機制】如果上面搜尋落空，直接強制抓一個景點補位
                        if not best_spot and not filtered_df.empty:
                            raw_row = filtered_df.iloc[0] # 強制抓剩餘資料的第一筆
                            data = get_travel_data(current_loc, f"{city}{raw_row['Name']}", transport_mode)
                            if not data: # 連 API 都失敗時的最後防線
                                data = {"dist_txt": "計算中", "dur_txt": "15 分鐘", "dur_sec": 900}
                            best_spot = raw_row.to_dict()
                            best_spot['travel'], best_spot['idx'] = data, filtered_df.index[0]

                        if best_spot:
                            spots_found += 1
                            st.markdown(f"### 第 {i+1} 站：{best_spot['Name']}")
                            if pd.notna(best_spot.get('Picture1')):
                                st.image(best_spot['Picture1'], use_container_width=True)
                            
                            desc = str(best_spot.get('Description', ''))
                            if desc == 'nan' or len(desc) < 5:
                                desc = f"位於{city}的精選景點，適合全家大小一同前往。"
                            st.write(f"📖 **景點特色**：{desc[:100]}...")
                            st.caption(f"🚗 交通：{best_spot['travel']['dist_txt']} (約 {best_spot['travel']['dur_txt']})")
                            
                            daily_sec += best_spot['travel']['dur_sec']
                            current_loc = f"{city}{best_spot['Name']}"
                            filtered_df = filtered_df.drop(best_spot['idx'])
                    
                    if spots_found == 0:
                        st.write("⚠️ 該區景點用盡，請嘗試更換縣市或增加搜尋範圍。")
                    else:
                        st.success(f"🌙 今日累計交通：{daily_sec // 60} 分鐘")
