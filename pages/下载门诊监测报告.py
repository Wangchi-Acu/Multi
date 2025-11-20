# pages/下载门诊监测报告.py
import streamlit as st
import pymysql
import os
import base64
from dotenv import load_dotenv
# 移除 streamlit_pdf_viewer 导入，如果不需要其他功能的话
# from streamlit_pdf_viewer import pdf_viewer 
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
            # --- 最快的 PDF 预览方法 ---
            try:
                # 方法1: 尝试使用 st.components.v1.html 和 iframe
                import streamlit.components.v1 as components
                import base64
                b64_pdf = base64.b64encode(blob).decode("utf-8")
                pdf_display = f"""
                <iframe 
                    src="data:application/pdf;base64,{b64_pdf}" 
                    width="100%" 
                    height="800px" 
                    type="application/pdf">
                </iframe>
                """
                components.html(pdf_display, height=850) # 高度略大于 iframe，确保显示完整
            except:
                # 方法2: 如果方法1失败，尝试直接 st.download_button 的数据方式展示（某些浏览器支持）
                # 这个方法不一定在所有环境下都有效，但速度快
                st.write("尝试预览...")
                st.markdown(f'<embed src="data:application/pdf;base64,{base64.b64encode(blob).decode()}" width="100%" height="800px" type="application/pdf">', unsafe_allow_html=True)
                # 如果以上都不行，提示用户下载后查看
                st.warning("PDF 预览可能不支持，请尝试下载后查看。")

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
