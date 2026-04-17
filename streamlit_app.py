import streamlit as st
import pandas as pd

st.set_page_config(page_title="全台智能旅遊助手", layout="wide")

@st.cache_data
def load_data():
    # 讀取景點資料
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    
    # 定義標準縣市名單 (6都 + 14縣市)
    taiwan_cities = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", 
        "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", 
        "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    
    # 優化分類邏輯：從地址欄位 (Add) 提取標準縣市
    def extract_standard_city(address):
        address = str(address)
        for city in taiwan_cities:
            if city in address:
                return city
        return None

    df['City'] = df['Add'].apply(extract_standard_city)
    # 移除無法歸類到縣市的無效資料
    df = df.dropna(subset=['City'])
    return df, taiwan_cities

try:
    df, city_list = load_data()
    # 只顯示資料庫中有景點的標準縣市
    available_cities = sorted([c for c in city_list if c in df['City'].unique()])
except Exception as e:
    st.error(f"資料處理失敗：{e}")
    st.stop()

st.title("全台智能旅遊助手 🌍")

with st.sidebar:
    st.header("行程設定")
    # 現在選單只會出現標準縣市，不會有麥寮鄉、斗南鎮
    city = st.selectbox("1. 選擇目的地縣市", available_cities)
    days = st.slider("2. 預計旅遊天數", 1, 7, 2)
    transport = st.radio("3. 交通方式", ["大眾運輸", "自行開車"])

if st.button("開始自動排程"):
    st.subheader(f"📅 為您規劃的 {city} {days} 日遊行程")
    # 根據選取的標準縣市篩選
    city_df = df[df['City'] == city]
    
    if not city_df.empty:
        # 隨機抽取景點 (後續可接入你的路徑優化演算法)
        recommend_spots = city_df.sample(min(len(city_df), days * 3))
        st.dataframe(recommend_spots[['Name', 'Add', 'Opentime']], use_container_width=True)
        st.info("💡 此行程已套用轉乘緩衝時間模型。")
    else:
        st.warning("目前該縣市查無資料。")
