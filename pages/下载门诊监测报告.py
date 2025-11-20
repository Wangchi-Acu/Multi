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

if st.button("立即下载"):
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
            # 修改查询以获取所有报告记录及其上传时间（或治疗日期字段，如果有的话）
            # 假设数据库中有 upload_time 或其他日期字段来区分报告
            cur.execute(
                "SELECT pdf_blob, upload_time, id FROM sleep_report_pdf WHERE patient_name=%s ORDER BY upload_time DESC",
                (name,))
            rows = cur.fetchall()

        if not rows:
            st.error("未找到您的报告，请确认姓名是否正确或稍后再试。")
            st.stop()

        st.success(f"找到 {len(rows)} 份报告，请选择您要查看或下载的报告：")

        # 为每份报告创建一个分列容器，或使用 st.expander 以节省空间
        for idx, (pdf_blob, upload_time, report_id) in enumerate(rows):
            # 使用 expander 来组织每个报告的选项，避免页面过长
            with st.expander(f"报告 #{idx+1} - 上传时间: {upload_time}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    # 使用 base64 编码的 PDF 在新标签页中预览
                    pdf_base64 = base64.b64encode(pdf_blob).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="500" type="application/pdf"></iframe>'
                    if st.button(f"📖 查看报告 #{idx+1}", key=f"view_{report_id}"):
                        # 在 Streamlit 中直接显示 PDF 预览
                        st.markdown(pdf_display, unsafe_allow_html=True)
                
                with col2:
                    # 下载按钮
                    st.download_button(
                        label=f"⬇️ 下载报告 #{idx+1}",
                        data=pdf_blob,
                        file_name=f"{name}_门诊监测报告_{upload_time}.pdf",
                        mime="application/pdf",
                        key=f"download_{report_id}"
                    )

    except Exception as e:
        st.error(f"数据库连接或查询出错: {e}")
    finally:
        if conn:
            conn.close()
