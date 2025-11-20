# pages/下载门诊监测报告.py
import streamlit as st
import pymysql
import os
from dotenv import load_dotenv
import base64

load_dotenv()

st.set_page_config(page_title="下载门诊监测报告", layout="wide")
st.title("📄 下载门诊监测报告")
st.markdown("---")

name = st.text_input("请输入您的姓名：").strip()

# 初始化 session state 用于存储查询到的报告
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'selected_report' not in st.session_state:
    st.session_state.selected_report = None

if st.button("点击查看已有报告"):
    if not name:
        st.warning("姓名不能为空")
        st.stop()

    conn = None
    try:
        conn = pymysql.connect(
            host=os.getenv('SQLPUB_HOST'),
            port=int(os.getenv('SQLPUB_PORT', 3307)),
            user=os.getenv('SQLPUB_USER'),
            password=os.getenv('SQLPUB_PWD'),
            db=os.getenv('SQLPUB_DB'),
            charset='utf8mb4')

        with conn.cursor() as cur:
            # 修改查询，使用 treat_date 替代 upload_time
            cur.execute(
                "SELECT pdf_blob, treat_date, id, upload_time FROM sleep_report_pdf WHERE patient_name=%s ORDER BY treat_date DESC",
                (name,))
            rows = cur.fetchall()

        if not rows:
            st.error("未找到您的报告，请确认姓名是否正确或稍后再试。")
            st.session_state.reports = [] # 清空之前的数据
        else:
            st.session_state.reports = rows
            st.success(f"成功获取到 {len(rows)} 份报告，请在下方选择操作。")
            # 显示报告列表
            for idx, (pdf_blob, treat_date, report_id, upload_time) in enumerate(st.session_state.reports):
                st.write(f"**报告 #{idx+1} - 治疗日期: {treat_date} (上传时间: {upload_time})**")

    except Exception as e:
        st.error(f"数据库连接或查询出错: {e}")
        st.session_state.reports = []
    finally:
        if conn:
            conn.close()

# 如果查询到了报告，则显示操作选项
if st.session_state.reports:
    st.markdown("---")
    st.subheader("选择报告进行操作")
    
    # 创建一个列表，包含每个报告的显示名称，使用 treat_date，用于选择
    report_options = []
    for idx, (pdf_blob, treat_date, report_id, upload_time) in enumerate(st.session_state.reports):
        report_options.append(f"报告 #{idx+1} - 治疗日期: {treat_date}")

    # 让用户选择一个报告
    selected_option = st.selectbox("请选择您要操作的报告：", report_options)

    # 根据选择的报告，找到对应的 blob 数据和相关信息
    selected_idx = report_options.index(selected_option)
    selected_pdf_blob, selected_treat_date, selected_report_id, selected_upload_time = st.session_state.reports[selected_idx]

    # 为选中的报告提供查看和下载按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"📖 查看报告 (治疗日期: {selected_treat_date})"):
            # 使用 base64 编码的 PDF 在页面中预览
            pdf_base64 = base64.b64encode(selected_pdf_blob).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
    
    with col2:
        st.download_button(
            label=f"⬇️ 下载报告 (治疗日期: {selected_treat_date})",
            data=selected_pdf_blob,
            file_name=f"{name}_门诊监测报告_治疗日期_{selected_treat_date}.pdf",
            mime="application/pdf",
        )
else:
    st.info("请先输入姓名并点击 '点击查看已有报告'。")
