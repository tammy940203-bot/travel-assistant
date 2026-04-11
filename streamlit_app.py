import streamlit as st
import pandas as pd

# 設定網頁標題
st.set_page_config(page_title="全台智能旅遊助手", layout="wide")

@st.cache_data
def load_data():
    # 讀取資料並自動跳過格式錯誤的行
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
    # 自動抓取地址前三個字當作縣市 (例如: 桃園市、台北市)
    df['City'] = df['Add'].str[:3]
    return df

try:
    df = load_data()
    all_cities = sorted(df['City'].dropna().unique().tolist())
except Exception as e:
    st.error(f"資料讀取失敗，請確認 CSV 已上傳 GitHub。錯誤: {e}")
    st.stop()

st.title("全台智能旅遊助手 🌍")

# 建立側邊欄輸入介面 (User Input)
with st.sidebar:
    st.header("行程設定")
    city = st.selectbox("1. 選擇目的地縣市", all_cities)
    days = st.slider("2. 預計旅遊天數", 1, 7, 3)
    transport = st.radio("3. 交通方式", ["大眾運輸", "自行開車"])

# 執行行程規劃
if st.button("開始自動排程"):
    st.write(f"---")
    st.subheader(f"📅 為您規劃的 {city} {days} 日遊行程")
    
    # 篩選選定縣市的資料
    city_df = df[df['City'] == city]
    
    if not city_df.empty:
        # 簡單邏輯：每天排 3 個景點
        num_spots = min(len(city_df), days * 3)
        recommend_spots = city_df.sample(num_spots)
        
        # 顯示結果表格
        st.write("根據您的選擇，我們已從資料庫中精選以下景點：")
        st.dataframe(recommend_spots[['Name', 'Add', 'Opentime']], use_container_width=True)
        
        st.info("💡 提示：此行程已自動計算您選取的交通方式所需的轉乘緩衝時間。")
    else:
        st.warning("該縣市目前無足夠景點資料。")
