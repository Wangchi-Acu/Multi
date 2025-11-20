# pages/下载门诊监测报告.py
import streamlit as st
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="下载门诊监测报告", layout="wide")
st.title("📄 下载门诊监测报告")
st.markdown("---")

name = st.text_input("请输入您的姓名：").strip()

# ---------- 全局缓存 ----------
@st.cache_data(show_spinner=False, ttl=60)          # 同一人 60 s 复用
def list_report_meta(patient_name: str):
    conn = pymysql.connect(
        host=os.getenv('SQLPUB_HOST'),
        port=int(os.getenv('SQLPUB_PORT', 3307)),
        user=os.getenv('SQLPUB_USER'),
        password=os.getenv('SQLPUB_PWD'),
        db=os.getenv('SQLPUB_DB'),
        charset='utf8mb4'
    )
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, treat_date, upload_time
            FROM sleep_report_pdf
            WHERE patient_name = %s
            ORDER BY treat_date DESC
        """, (patient_name,))
        rows = cur.fetchall()
    conn.close()
    return rows


@st.cache_data(show_spinner=False, ttl=300)         # 同一份报告 5 min 复用
def get_blob_by_id(report_id: int) -> bytes:
    conn = pymysql.connect(
        host=os.getenv('SQLPUB_HOST'),
        port=int(os.getenv('SQLPUB_PORT', 3307)),
        user=os.getenv('SQLPUB_USER'),
        password=os.getenv('SQLPUB_PWD'),
        db=os.getenv('SQLPUB_DB'),
        charset='utf8mb4'
    )
    with conn.cursor() as cur:
        cur.execute("SELECT pdf_blob FROM sleep_report_pdf WHERE id = %s", (report_id,))
        (blob,) = cur.fetchone()
    conn.close()
    return blob


# ---------- session 初始化 ----------
if "meta_list" not in st.session_state:
    st.session_state.meta_list = []

# ---------- 1. 查列表 ----------
if st.button("点击查看已有报告"):
    if not name:
        st.warning("姓名不能为空")
        st.stop()
    with st.spinner("正在加载报告列表…"):
        st.session_state.meta_list = list_report_meta(name)
    if not st.session_state.meta_list:
        st.error("未找到您的报告，请确认姓名是否正确或稍后再试。")

# ---------- 2. 展示列表 ----------
if st.session_state.meta_list:
    st.markdown("---")
    st.subheader("选择报告进行下载")

    report_options = []
    for idx, row in enumerate(st.session_state.meta_list):
        _, treat_date_str, _ = row
        # 将 YYYYMMDD 格式转换为 YYYY年MM月DD日 格式
        try:
            year = treat_date_str[:4]
            month = treat_date_str[4:6]
            day = treat_date_str[6:8]
            formatted_date = f"{year}年{month.zfill(2)}月{day.zfill(2)}日"
        except (IndexError, TypeError):
            # 如果格式不正确，回退到原始格式
            formatted_date = treat_date_str
        
        report_options.append(f"报告 #{idx+1} - 治疗日期: {formatted_date}")

    selected_option = st.selectbox("请选择您要下载的报告：", report_options)
    selected_idx = report_options.index(selected_option)
    selected_id, selected_treat_date_str, selected_upload = st.session_state.meta_list[selected_idx]

    # 将选定的治疗日期也转换为 YYYY年MM月DD日 格式用于下载按钮
    try:
        year = selected_treat_date_str[:4]
        month = selected_treat_date_str[4:6]
        day = selected_treat_date_str[6:8]
        selected_formatted_date = f"{year}年{month.zfill(2)}月{day.zfill(2)}日"
    except (IndexError, TypeError):
        selected_formatted_date = selected_treat_date_str

    # 只保留下载按钮
    blob = get_blob_by_id(selected_id)
    st.download_button(
        label=f"⬇️ 下载报告 (治疗日期: {selected_formatted_date})",
        data=blob,
        file_name=f"{name}_门诊监测报告_治疗日期_{selected_treat_date_str}.pdf",
        mime="application/pdf"
    )
else:
    st.info("请先输入姓名并点击 '点击查看已有报告'。")
