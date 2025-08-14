import streamlit as st
import pandas as pd
import pymysql
import os
import plotly.express as px
from datetime import date

st.set_page_config(page_title="睡眠日记查询", layout="wide")
st.title("📊 睡眠日记查询")

pwd = st.text_input("查询密码", type="password")
if pwd.strip() != "10338":
    st.stop()

tab1, tab2 = st.tabs(["🔍 单次查询", "📈 最近7次汇总"])

def run_query(sql, params=None):
    conn = pymysql.connect(
        host=os.getenv("SQLPUB_HOST"),
        port=int(os.getenv("SQLPUB_PORT", 3307)),
        user=os.getenv("SQLPUB_USER"),
        password=os.getenv("SQLPUB_PWD"),
        database=os.getenv("SQLPUB_DB"),
        charset="utf8mb4"
    )
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df

with tab1:
    patient = st.text_input("患者姓名").strip()
    record_date = st.date_input("记录日期", date.today())
    if st.button("查询单次") and patient:
        df = run_query(
            "SELECT * FROM sleep_diary WHERE name=%s AND record_date=%s ORDER BY created_at DESC",
            params=(patient, record_date.isoformat())
        )
        st.dataframe(df.T if not df.empty else "暂无记录")

with tab2:
    patient = st.text_input("患者姓名（汇总）").strip()
    if st.button("查询最近7次") and patient:
        df = run_query(
            "SELECT * FROM sleep_diary WHERE name=%s ORDER BY record_date DESC LIMIT 7",
            params=(patient,)
        )
        if df.empty:
            st.warning("暂无记录")
        else:
            df = df.sort_values("record_date")
            df["date_fmt"] = pd.to_datetime(df["record_date"]).dt.strftime("%m-%d")
            cols = ["total_sleep_hours", "sleep_quality", "sleep_latency", "night_awake_count"]
            df_plot = df[["date_fmt"] + cols].melt(id_vars="date_fmt", var_name="指标", value_name="值")
            fig = px.line(df_plot, x="date_fmt", y="值", color="指标", markers=True,
                          title=f"{patient} 最近7次睡眠关键指标")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df.reset_index(drop=True))
