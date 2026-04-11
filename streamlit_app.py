import streamlit as st
import pandas as pd

# 讀取資料 (加上快取，網頁才不會卡)
@st.cache_data
def load_data():
    # 確保 CSV 已經上傳到 GitHub 跟這個 py 檔放在一起
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    # 提取縣市名稱 (通常在 'Add' 欄位的前三個字)
    df['City'] = df['Add'].str[:3]
    return df

df = load_data()

st.title("全台智能旅遊助手 🌍")

with st.sidebar:
    st.header("行程設定")
    # 自動抓取資料中所有的縣市，去除重複並排序
    all_cities = sorted(df['City'].unique().tolist())
    city = st.selectbox("選擇目的地縣市", all_cities)
    days = st.slider("旅遊天數", 1, 7, 3)

# 執行排程
if st.button("開始自動排程"):
    st.write(f"正在為您從 4,928 筆數據中規劃 **{city}** 的行程...")
    
    # 篩選該縣市的資料
    city_df = df[df['City'] == city]
    
    if not city_df.empty:
        # 隨機挑選幾個景點展示 (示範用)
        recommend_spots = city_df.sample(min(len(city_df), days * 3))
        st.subheader(f"📍 {city} 推薦清單")
        st.dataframe(recommend_spots[['Name', 'Add', 'Opentime']])
    else:
        st.warning("找不到該縣市的景點，請檢查資料格式。")
