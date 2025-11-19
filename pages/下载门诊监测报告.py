# pages/下载门诊监测报告.py
import streamlit as st
import pymysql, os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="下载门诊监测报告", layout="centered")
st.title("📄 下载门诊监测报告")
st.markdown("---")

name = st.text_input("请输入您的姓名：").strip()
if st.button("立即下载"):
    if not name:
        st.warning("姓名不能为空")
        st.stop()

    conn = pymysql.connect(
        host=os.getenv('SQLPUB_HOST'),
        port=int(os.getenv('SQLPUB_PORT', 3307)),
        user=os.getenv('SQLPUB_USER'),
        password=os.getenv('SQLPUB_PWD'),
        db=os.getenv('SQLPUB_DB'),
        charset='utf8mb4')

    with conn.cursor() as cur:
        cur.execute(
            "SELECT pdf_blob FROM sleep_report_pdf WHERE patient_name=%s ORDER BY upload_time DESC LIMIT 1",
            (name,))
        row = cur.fetchone()

    if row is None:
        st.error("未找到您的报告，请确认姓名是否正确或稍后再试。")
        st.stop()

    st.success("正在下载，请稍候...")
    st.download_button(
        label="⬇ 点我保存 PDF",
        data=row[0],
        file_name=f"{name}_门诊监测报告.pdf",
        mime="application/pdf"
    )
