import streamlit as st
import pandas as pd

st.set_page_config(page_title="全台智能旅遊助手", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    
    # 定義台灣標準縣市清單，確保選單不會太細碎
    taiwan_cities = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
        "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣", 
        "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", 
        "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    
    # 建立一個新的 City 欄位，檢查地址中是否包含上述縣市名稱
    def get_city(address):
        for city in taiwan_cities:
            if city in str(address):
                return city
        return "其他" # 若沒對應到則歸類為其他
        
    df['City'] = df['Add'].apply(get_city)
    return df, taiwan_cities

try:
    df, city_list = load_data()
    # 只顯示資料庫中實際存在的縣市，且過濾掉「其他」
    available_cities = [c for c in city_list if c in df['City'].unique()]
except Exception as e:
    st.error(f"資料讀取失敗: {e}")
    st.stop()

st.title("全台智能旅遊助手 🌍")

with st.sidebar:
    st.header("行程設定")
    city = st.selectbox("1. 選擇目的地縣市", available_cities)
    days = st.slider("2. 預計旅遊天數", 1, 7, 2)
    transport = st.radio("3. 交通方式", ["大眾運輸", "自行開車"])

if st.button("開始自動排程"):
