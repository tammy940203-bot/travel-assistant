import streamlit as st
import pandas as pd
import requests

# 1. 安全金鑰讀取
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
except:
    st.error("❌ 找不到 API 金鑰！")
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

st.set_page_config(page_title="智能旅遊助手 V4.7", layout="wide")
st.title("全台智能旅遊助手 V4.7 (行程滿載版) 🌍")

with st.sidebar:
    st.header("⚙️ 行程設定")
    days = st.slider("預計旅遊天數", 1, 7, 3)
    city = st.selectbox("選擇目的縣市", ["臺北市", "宜蘭縣", "新北市", "桃園市", "臺中市", "高雄市", "屏東縣"])
    transport_mode = st.radio("交通方式", ["driving", "transit", "walking"])
    start_point = st.text_input("🚩 第一天出發起點", "臺北車站")
    hotel_addr = st.text_input("🏨 住宿/終點名稱", "台北市飯店")

if st.button("🚀 生成豐富行程 (保證有內容)"):
    if df is not None:
        # 過濾黑名單但保持廣度
        exclude = ['書局', '書店', '圖書館', '補習班', '藥局', '診所', '辦事處']
        main_df = df[df['Add'].str.contains(city, na=False)].copy()
        main_df = main_df[~main_df['Name'].str.contains('|'.join(exclude), na=False)]
        
        if main_df.empty:
            st.warning("資料庫中此縣市景點不足！")
        else:
            # 準備已使用景點清單，避免重複
            used_names = []

            for day in range(1, days + 1):
                with st.expander(f"📅 第 {day} 天行程規劃", expanded=True):
                    current_loc = start_point if day == 1 else hotel_addr
                    daily_sec = 0
                    
                    # 每天強行產生 3 個點
                    for i in range(3):
                        # 排除已選過的點
                        available_df = main_df[~main_df['Name'].isin(used_names)]
                        if available_df.empty: break
                        
                        # 抽樣 50 個點 (擴大範圍)
                        candidates = available_df.sample(min(50, len(available_df)))
                        best_spot = None
                        
                        # 1. 先嘗試找「順路」的點 (單趟 < 40 分鐘)
                        for idx, row in candidates.iterrows():
                            data = get_travel_data(current_loc, f"{city}{row['Name']}", transport_mode)
                            if data and data['dur_sec'] < 2400: # 40 分鐘
                                best_spot = row.to_dict()
                                best_spot['travel'], best_spot['idx'] = data, idx
                                break
                        
                        # 2. 【保底】如果找不到順路的，就從候選中隨機硬抓一個！
                        if not best_spot:
                            lucky_row = candidates.iloc[0]
                            data = get_travel_data(current_loc, f"{city}{lucky_row['Name']}", transport_mode)
                            # 如果 API 還是掛了，就給預設值
                            if not data: data = {"dist_txt": "計算中", "dur_txt": "15 分鐘", "dur_sec": 900}
                            best_spot = lucky_row.to_dict()
                            best_spot['travel'], best_spot['idx'] = data, lucky_row.name

                        if best_spot:
                            st.markdown(f"### 第 {i+1} 站：{best_spot['Name']}")
                            # 顯示圖片
                            if pd.notna(best_spot.get('Picture1')):
                                st.image(best_spot['Picture1'], use_container_width=True)
                            
                            # 描述處理
                            desc = str(best_spot.get('Description', ''))
                            if desc == 'nan' or len(desc) < 5:
                                desc = f"位於{city}的熱門觀光據點，推薦您排入行程。"
                            st.write(f"📖 **景點特色**：{desc[:100]}...")
                            st.caption(f"🚗 交通：{best_spot['travel']['dist_txt']} (約 {best_spot['travel']['dur_txt']})")
                            
                            daily_sec += best_spot['travel']['dur_sec']
                            current_loc = f"{city}{best_spot['Name']}"
                            used_names.append(best_spot['Name'])
                            st.markdown("---")

                    st.success(f"🌙 今日總交通耗時：{daily_sec // 60} 分鐘")
    else:
        st.error("找不到 CSV 資料庫。")
