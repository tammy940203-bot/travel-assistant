import streamlit as st
import pandas as pd
import requests

# 1. 從 Secrets 讀取金鑰
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 設定 MAPS_API_KEY")
    st.stop()

# 2. 定義 Google Maps 請求函式
def get_travel_data(origin, destination, mode):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin, "destinations": destination,
        "mode": mode, "language": "zh-TW", "key": API_KEY
    }
    try:
        res = requests.get(url, params=params).json()
        if res['status'] == 'OK':
            element = res['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                return {
                    "dist_txt": element['distance']['text'],
                    "dur_txt": element['duration']['text'],
                    "dur_sec": element['duration']['value']
                }
        return None
    except:
        return None

# --- 資料載入 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('Scenic_Spot_C_f.csv')
        return df
    except:
        return None

df = load_data()

# --- UI 介面 ---
st.set_page_config(page_title="智能旅遊助手", layout="wide")
st.title("全台智能旅遊助手 V4.3 (穩定版) 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "宜蘭縣", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", 
        "嘉義縣", "屏東縣", "花蓮縣", "臺東縣"
    ])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], index=0)
    
    start_point = st.text_input("🚩 設定第一天出發點", "臺北車站")
    hotel_addr = st.text_input("🏨 設定每日住宿點", "台北市飯店")

# --- 核心邏輯 ---
if st.button("🚀 生成順路且有趣的行程"):
    if df is not None:
        # 【黑名單過濾】徹底排除非觀光景點
        exclude_list = ['書局', '書店', '圖書館', '補習班', '藥局', '診所', '服務處', '辦事處']
        pattern = '|'.join(exclude_list)
        
        filtered_df = df[df['Add'].str.contains(city, na=False)].copy()
        filtered_df = filtered_df[~filtered_df['Name'].str.contains(pattern, na=False)]
        
        if filtered_df.empty:
            st.warning("過濾後找不到適合的景點。")
        else:
            MAX_DUR_SEC = 3 * 3600 # 每日交通上限 3 小時
            
            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    current_loc = start_point if day == 1 else hotel_addr
                    daily_total_sec = 0
                    
                    for i in range(3): 
                        if filtered_df.empty: break
                        
                        # 從 15 個候選點選最近的，確保順路又有多樣性
                        candidates = filtered_df.sample(min(15, len(filtered_df)))
                        best_spot = None
                        min_dur = float('inf')

                        for idx, row in candidates.iterrows():
                            data = get_travel_data(current_loc, f"{city}{row['Name']}", transport_mode)
                            if data and (daily_total_sec + data['dur_sec'] <= MAX_DUR_SEC):
                                if data['dur_sec'] < min_dur:
                                    min_dur = data['dur_sec']
                                    best_spot = row.to_dict()
                                    best_spot['travel'] = data
                                    best_spot['idx'] = idx

                        if best_spot:
                            st.markdown(f"### 第 {i+1} 站：{best_spot['Name']}")
                            
                            # 圖片防呆
                            pic = best_spot.get('Picture1')
                            if pd.notna(pic) and str(pic).startswith('http'):
                                st.image(pic, use_container_width=True)
                            
                            # 【關鍵修復】先轉字串再切片，防止 NaN 導致閃退
                            desc = str(best_spot.get('Description', '暫無描述資料'))
                            st.write(f"📖 **景點特色**：{desc[:100]}...")
                            
                            st.caption(f"🚗 交通：移動 {best_spot['travel']['dist_txt']} (約 {best_spot['travel']['dur_txt']})")
                            st.markdown("---")
                            
                            daily_total_sec += best_spot['travel']['dur_sec']
                            current_loc = f"{city}{best_spot['Name']}"
                            filtered_df = filtered_df.drop(best_spot['idx'])

                    # 回程計算
                    back = get_travel_data(current_loc, hotel_addr, transport_mode)
                    if back:
                        daily_total_sec += back['dur_sec']
                        st.success(f"🌙 今日交通總計：{daily_total_sec // 60} 分鐘 (限額 180 分鐘)")
    else:
        st.error("找不到資料庫 CSV。")
