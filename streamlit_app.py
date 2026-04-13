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
        return None
    except: return None

@st.cache_data
def load_data():
    try: return pd.read_csv('Scenic_Spot_C_f.csv')
    except: return None

df = load_data()

st.set_page_config(page_title="智能旅遊助手 V4.4", layout="wide")
st.title("全台智能旅遊助手 V4.4 (最終強韌版) 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "宜蘭縣", "花蓮縣"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_point = st.text_input("🚩 第一天起點", "臺北車站")
    hotel_addr = st.text_input("🏨 每日住宿點", "台北市飯店")

if st.button("🚀 生成最優行程"):
    if df is not None:
        # 排除非觀光點
        exclude = ['書局', '書店', '圖書館', '補習班', '藥局', '診所', '服務處']
        filtered_df = df[df['Add'].str.contains(city, na=False)].copy()
        filtered_df = filtered_df[~filtered_df['Name'].str.contains('|'.join(exclude), na=False)]
        
        if filtered_df.empty:
            st.warning("找不到景點。")
        else:
            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    current_loc = start_point if day == 1 else hotel_addr
                    daily_sec = 0
                    
                    # 嘗試抓 3 個點
                    for i in range(3):
                        if filtered_df.empty: break
                        
                        # 擴大抽樣至 20 個點，增加成功機率
                        candidates = filtered_df.sample(min(20, len(filtered_df)))
                        best_spot = None
                        
                        for idx, row in candidates.iterrows():
                            data = get_travel_data(current_loc, f"{city}{row['Name']}", transport_mode)
                            if data:
                                # 只要不超過單次 1 小時車程就接受，確保有行程
                                if data['dur_sec'] < 3600:
                                    best_spot = row.to_dict()
                                    best_spot['travel'], best_spot['idx'] = data, idx
                                    break # 找到第一個合適的就出發

                        if best_spot:
                            st.markdown(f"### 第 {i+1} 站：{best_spot['Name']}")
                            # 圖片顯示
                            if pd.notna(best_spot.get('Picture1')):
                                st.image(best_spot['Picture1'], use_container_width=True)
                            
                            # 修正 nan 顯示問題
                            desc = str(best_spot.get('Description', ''))
                            if desc == 'nan' or len(desc) < 5:
                                desc = "這是一個位於" + city + "的熱門景點，適合規劃於行程中。"
                            st.write(f"📖 **景點特色**：{desc[:100]}...")
                            st.caption(f"🚗 {best_spot['travel']['dist_txt']} (約 {best_spot['travel']['dur_txt']})")
                            
                            daily_sec += best_spot['travel']['dur_sec']
                            current_loc = f"{city}{best_spot['Name']}"
                            filtered_df = filtered_df.drop(best_spot['idx'])
                    
                    st.success(f"🌙 今日累計交通：{daily_sec // 60} 分鐘")
