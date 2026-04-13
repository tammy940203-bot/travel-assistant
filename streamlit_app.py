import streamlit as st
import pandas as pd
import requests

# 1. 從 Secrets 讀取金鑰
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except Exception:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 設定 MAPS_API_KEY")
    st.stop()

# 2. 定義 Google Maps 請求函式 (回傳秒數與文字描述)
def get_travel_data(origin, destination, mode):
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
            if element['status'] == 'OK':
                return {
                    "dist_txt": element['distance']['text'],
                    "dur_txt": element['duration']['text'],
                    "dur_sec": element['duration']['value']  # 用秒數來做計算排序
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
st.set_page_config(page_title="智能旅遊助手 V4.0", layout="wide")
st.title("全台智能旅遊助手 V4.0 (順路優化版) 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "宜蘭縣", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", 
        "嘉義縣", "屏東縣", "花蓮縣", "臺東縣"
    ])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"], 
                              format_func=lambda x: {"driving": "自行開車", "transit": "大眾運輸", "walking": "步行"}[x])
    
    start_point = st.text_input("🚩 設定第一天出發點", "臺北車站")
    hotel_addr = st.text_input("🏨 設定每日住宿點", "台北某某飯店")

# --- 核心優化邏輯 ---
if st.button("🚀 生成順路且不塞車行程"):
    if df is not None:
        # 篩選縣市景點
        filtered_df = df[df['Add'].str.contains(city, na=False)].copy()
        
        if filtered_df.empty:
            st.warning("找不到該縣市的景點，請檢查資料庫。")
        else:
            # 每日限制：總車程不超過 3 小時 (10800 秒)
            MAX_DUR_SEC = 3 * 3600 
            
            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    current_loc = start_point if day == 1 else hotel_addr
                    daily_total_sec = 0
                    daily_spots = []

                    # 每一天嘗試找 3 個景點
                    for _ in range(3):
                        if filtered_df.empty: break
                        
                        # 隨機挑選 8 個候選點計算距離 (避免 API 呼叫過多)
                        candidates = filtered_df.sample(min(8, len(filtered_df)))
                        best_spot = None
                        min_dist_sec = float('inf')

                        for idx, row in candidates.iterrows():
                            # 加上縣市名搜尋更精準
                            target = f"{city}{row['Name']}"
                            data = get_travel_data(current_loc, target, transport_mode)
                            
                            if data:
                                # 檢查：如果加入這站會不會讓「當天總交通時間」爆表
                                if daily_total_sec + data['dur_sec'] <= MAX_DUR_SEC:
                                    if data['dur_sec'] < min_dist_sec:
                                        min_dist_sec = data['dur_sec']
                                        best_spot = {"name": row['Name'], "data": data, "idx": idx}

                        if best_spot:
                            daily_spots.append(best_spot)
                            daily_total_sec += best_spot['data']['dur_sec']
                            current_loc = f"{city}{best_spot['name']}"
                            # 移除已選點
                            filtered_df = filtered_df.drop(best_spot['idx'])

                    # 顯示行程
                    if not daily_spots:
                        st.write("這附近找不到更近的點了，請調整起點或交通工具。")
                    else:
                        for i, s in enumerate(daily_spots):
                            st.markdown(f"**第 {i+1} 站：{s['name']}**")
                            st.caption(f"⏱️ 移動距離：{s['data']['dist_txt']} (約 {s['data']['dur_txt']})")
                        
                        # 最後回飯店
                        back_home = get_travel_data(current_loc, hotel_addr, transport_mode)
                        if back_home:
                            daily_total_sec += back_home['dur_sec']
                            st.success(f"🌙 今日總交通耗時：{daily_total_sec // 60} 分鐘 (限制 180 分鐘內)")
    else:
        st.error("找不到景點資料庫 CSV 檔案。")
