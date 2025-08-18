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
            st.stop()

        df = df.sort_values("record_date")
        df["date_fmt"] = pd.to_datetime(df["record_date"]).dt.strftime("%m-%d")

        # ----- 工具：把时间字符串 → 分钟数 -----
        def time_to_min(t):
            try:
                h, m = map(int, t.split(":"))
                return h * 60 + m
            except:
                return None

        # 1. 关键时间折线图
        time_cols = ["bed_time", "try_sleep_time", "final_wake_time", "get_up_time",
                     "med_time", "nap_start", "nap_end"]
        df_time = df[["date_fmt"] + time_cols].copy()
        for col in time_cols:
            df_time[col] = df_time[col].apply(time_to_min)

        fig1 = px.line(df_time.melt(id_vars="date_fmt", var_name="事件", value_name="分钟"),
                       x="date_fmt", y="分钟", color="事件",
                       title=f"{patient} —— 关键时间折线图")
        st.plotly_chart(fig1, use_container_width=True)

        # 2. 入睡所需时长
        fig2 = px.line(df, x="date_fmt", y="sleep_latency",
                       markers=True, title=f"{patient} —— 入睡所需时长（分钟）")
        st.plotly_chart(fig2, use_container_width=True)

        # 3. 夜间觉醒次数
        fig3 = px.line(df, x="date_fmt", y="night_awake_count",
                       markers=True, title=f"{patient} —— 夜间觉醒次数")
        st.plotly_chart(fig3, use_container_width=True)

        # 4. 夜间觉醒总时长
        fig4 = px.line(df, x="date_fmt", y="night_awake_total",
                       markers=True, title=f"{patient} —— 夜间觉醒总时长（分钟）")
        st.plotly_chart(fig4, use_container_width=True)

        # 5. 总睡眠时长
        fig5 = px.line(df, x="date_fmt", y="total_sleep_hours",
                       markers=True, title=f"{patient} —— 总睡眠时长（小时）")
        st.plotly_chart(fig5, use_container_width=True)

        # 原始数据表
        st.dataframe(df.reset_index(drop=True))
