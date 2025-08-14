import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os

st.set_page_config(page_title="睡眠日记查询", layout="wide")
st.title("📊 睡眠日记查询")

# 1. 密码校验
pwd = st.text_input("请输入查询密码", type="password")
if pwd.strip() != "10338":
    st.stop()

# 2. 数据库连接
@st.cache_data(ttl=60)
def get_conn():
    return pymysql.connect(
        host=os.getenv("SQLPUB_HOST"),
        port=int(os.getenv("SQLPUB_PORT", 3307)),
        user=os.getenv("SQLPUB_USER"),
        password=os.getenv("SQLPUB_PWD"),
        database=os.getenv("SQLPUB_DB"),
        charset="utf8mb4"
    )

# 3. 两种查询方式
tab1, tab2 = st.tabs(["🔍 单次查询", "📈 最近7次汇总"])

with tab1:
    st.subheader("单次睡眠日记查询")
    col1, col2 = st.columns(2)
    patient = col1.text_input("患者姓名").strip()
    record_date = col2.date_input("记录日期", date.today())
    if st.button("查询单次") and patient:
        sql = """
        SELECT * FROM sleep_diary
        WHERE name=%s AND record_date=%s
        ORDER BY created_at DESC
        LIMIT 1
        """
        df = pd.read_sql(sql, get_conn(), params=(patient, record_date.isoformat()))
        if df.empty:
            st.warning("该日期无记录")
        else:
            st.dataframe(df.T, use_container_width=True)

with tab2:
    st.subheader("最近7次汇总（折线图）")
    patient = st.text_input("患者姓名（汇总）").strip()
    if st.button("查询最近7次") and patient:
        sql = """
        SELECT * FROM sleep_diary
        WHERE name=%s
        ORDER BY record_date DESC
        LIMIT 7
        """
        df = pd.read_sql(sql, get_conn(), params=(patient,))
        if df.empty:
            st.warning("暂无记录")
        else:
            df = df.sort_values("record_date")  # 升序便于连线
            # 关键指标
            cols = ["record_date", "total_sleep_hours", "sleep_quality", "sleep_latency", "night_awake_count"]
            df_plot = df[cols].copy()
            df_plot["record_date"] = pd.to_datetime(df_plot["record_date"]).dt.strftime("%m-%d")

            # 多指标折线图
            fig = px.line(
                df_plot.melt(id_vars="record_date", var_name="指标", value_name="值"),
                x="record_date",
                y="值",
                color="指标",
                markers=True,
                title=f"{patient} 最近7次睡眠关键指标"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 表格
            st.subheader("原始数据")
            st.dataframe(df.reset_index(drop=True))
