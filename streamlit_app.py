import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    # 加入 error_bad_lines 防錯，並確保讀取檔名正確
    df = pd.read_csv('Scenic_Spot_C_f.csv', encoding='utf-8-sig', on_bad_lines='skip')
    # 清除欄位名稱可能有的空白，並建立 City 欄位
    df.columns = df.columns.str.strip()
    df['City'] = df['Add'].str[:3] 
    return df

try:
    df = load_data()
    all_cities = sorted(df['City'].dropna().unique().tolist()) # 加入 dropna() 避免空值報錯
except Exception as e:
    st.error(f"資料讀取失敗，請確認 CSV 檔案已上傳至 GitHub。錯誤訊息: {e}")
    st.stop()

st.title("全台智能旅遊助手 🌍")
# ... 後續介面代碼 ...
