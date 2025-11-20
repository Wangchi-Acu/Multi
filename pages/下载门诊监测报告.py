# pages/下载门诊监测报告.py
import streamlit as st
import pymysql
import os
import base64
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
    st.subheader("选择报告进行操作")

    report_options = [
        f"报告 #{idx+1} - 治疗日期: {row[1]}"
        for idx, row in enumerate(st.session_state.meta_list)
    ]
    selected_option = st.selectbox("请选择您要操作的报告：", report_options)
    selected_idx = report_options.index(selected_option)
    selected_id, selected_treat_date, selected_upload = st.session_state.meta_list[selected_idx]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📖 查看报告"):
            blob = get_blob_by_id(selected_id)
            b64 = base64.b64encode(blob).decode()
            html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(html, unsafe_allow_html=True)

    with col2:
        blob = get_blob_by_id(selected_id)
        st.download_button(
            label="⬇️ 下载报告",
            data=blob,
            file_name=f"{name}_门诊监测报告_治疗日期_{selected_treat_date}.pdf",
            mime="application/pdf"
        )
else:
    st.info("请先输入姓名并点击 '点击查看已有报告'。")
