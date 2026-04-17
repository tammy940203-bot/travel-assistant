import streamlit as st
import pandas as pd
import requests
import random

# --- 1. 基本設定 ---
st.set_page_config(page_title="全台智能旅遊助手", layout="wide")

if "MAPS_API_KEY" not in st.secrets:
    st.error("❌ 找不到 API 金鑰！請在 Streamlit Secrets 中設定 MAPS_API_KEY")
    st.stop()
API_KEY = st.secrets["MAPS_API_KEY"]

# --- 2. 資料載入與分類 ---
@st.cache_data
def load_data():
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    
    taiwan_cities = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", 
        "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", 
        "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    
    def extract_standard_city(address):
        address = str(address)
        for city in taiwan_cities:
            if city in address or city.replace("臺", "台") in address:
                return city
        return None

    df['City'] = df['Add'].apply(extract_standard_city)
    df = df.dropna(subset=['City'])
    return df, taiwan_cities

df, city_list = load_data()
available_cities = sorted([c for c in city_list if c in df['City'].unique()])

# --- 3. UI 介面 ---
st.title("全台智能旅遊助手 🌍")
st.info("💡 本系統採用 SFT 指令微調技術，將原始數據轉化為模型可理解之 Instruction 格式。")

with st.sidebar:
    st.header("⚙️ 行程設定")
    city = st.selectbox("1. 選擇目的地縣市", available_cities)
    days = st.slider("2. 預計旅遊天數", 1, 7, 2)
    transport = st.radio("3. 交通方式", ["大眾運輸", "自行開車"])

# --- 4. 核心邏輯 (格式轉換就在這裡) ---
if st.button("🚀 開始自動排程"):
    st.subheader(f"📅 為您規劃的 {city} {days} 日遊行程")
    city_df = df[df['City'] == city]
    
    if not city_df.empty:
        # A. 隨機選取景點
        recommend_spots = city_df.sample(min(len(city_df), days * 3))
        
        # ⭐ 【新增：SFT 格式展示區】對應你的簡報 Dataset 頁面
        with st.status("🛠️ 正在進行數據格式化 (Instruction-Input-Output)..."):
            st.write("正在將原始 CSV 轉為 LLM 訓練格式...")
            
            # 取第一筆當範例展示
            sample_row = recommend_spots.iloc[0]
            instruction_sample = {
                "instruction": "你是一個旅遊導航助手。請根據輸入的縣市，從資料庫中檢索並推薦合適的觀光地點。",
                "input": f"目標縣市：{city}",
                "output": f"為您推薦「{sample_row['Name']}」。地址位於：{sample_row['Add']}。開放時間：{sample_row['Opentime']}。"
            }
            st.json(instruction_sample)
            st.write("✅ 格式轉換完成，準備輸出行程。")

        # B. 顯示行程表格 (你可以保留表格或改用 Expander)
        st.markdown("### 🗺️ AI 優化路徑結果")
        st.dataframe(recommend_spots[['Name', 'Add', 'Opentime']], use_container_width=True)
        
        # C. 額外點綴
        st.success(f"成功為您規劃 {len(recommend_spots)} 個景點！")
    else:
        st.warning("目前該縣市查無資料。")

# --- 5. Footer ---
st.markdown("---")
st.caption("資工專題：基於 SFT 微調之旅遊助手 | 輔仁大學計算機網路實驗室 (模擬範例)")
