import streamlit as st
import pandas as pd
import pymysql
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="睡眠日记查询", layout="wide")
st.title("📊 睡眠日记查询")

pwd = st.text_input("查询密码", type="password")
if pwd.strip() != "10338":
    st.stop()

# 添加按日期查询所有记录的标签页
tab1, tab2, tab3 = st.tabs(["🔍 单次查询", "📈 最近7次汇总", "📅 按日期查询"])

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

# 时间转换函数（支持跨天）
def time_to_min(t):
    try:
        h, m = map(int, t.split(":"))
        # 处理跨天时间（如02:00表示为26:00）
        if h < 12 and h >= 0:
            h += 24
        return h * 60 + m
    except:
        return None

# 分钟数转时间字符串（用于图表标签）
def min_to_time(minutes):
    total_hours = minutes // 60
    total_minutes = minutes % 60
    return f"{total_hours:02d}:{total_minutes:02d}"

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
            """
            SELECT t1.* 
            FROM sleep_diary t1
            INNER JOIN (
                SELECT record_date, MAX(created_at) AS max_created_at
                FROM sleep_diary
                WHERE name = %s
                GROUP BY record_date
                ORDER BY record_date DESC
                LIMIT 7
            ) t2 
            ON t1.record_date = t2.record_date AND t1.created_at = t2.max_created_at
            ORDER BY t1.record_date ASC
            """,
            params=(patient,)
        )

        if df.empty:
            st.warning("暂无记录")
            st.stop()

        df["date_fmt"] = pd.to_datetime(df["record_date"]).dt.strftime("%m-%d")

        # ---------- 1. 夜间关键时间折线图 ----------
        night_time_cols = ["bed_time", "try_sleep_time", "final_wake_time", "get_up_time", "med_time"]
        night_time_labels = ["上床时间", "试图入睡时间", "最终醒来时间", "起床时间", "服药时间"]

        night_data = []
        for col, label in zip(night_time_cols, night_time_labels):
            minutes = df[col].apply(time_to_min)
            labels = df[col].tolist()

            night_data.append(go.Scatter(
                x=df["date_fmt"],
                y=minutes,
                name=label,
                mode='lines+markers+text',
                text=labels,
                textposition="top center",
                marker=dict(size=10),
                line=dict(width=3),
                textfont=dict(size=12, color='black')
            ))

        fig_night = go.Figure(data=night_data)

        # 设置 Y 轴为时间格式（分钟数），并自定义 tick labels
        tickvals = list(range(0, 1441, 120))  # 每两小时一个 tick
        ticktext = [min_to_time(m) for m in tickvals]

        fig_night.update_layout(
            title=f"{patient} —— 夜间关键时间点",
            xaxis_title="日期",
            yaxis=dict(
                title="时间",
                tickvals=tickvals,
                ticktext=ticktext,
                range=[0, 1440],  # 00:00 到 24:00
                autorange=False,
                type='linear',
                tickfont=dict(size=12),
            ),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=500
        )
        st.plotly_chart(fig_night, use_container_width=True)

        # ---------- 2. 日间小睡时间折线图 ----------
        nap_cols = ["nap_start", "nap_end"]
        nap_labels = ["小睡开始时间", "小睡结束时间"]

        nap_data = []
        for col, label in zip(nap_cols, nap_labels):
            minutes = df[col].apply(lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))
            labels = df[col].tolist()

            nap_data.append(go.Scatter(
                x=df["date_fmt"],
                y=minutes,
                name=label,
                mode='lines+markers+text',
                text=labels,
                textposition="top center",
                marker=dict(size=10),
                line=dict(width=3),
                textfont=dict(size=12, color='black')
            ))

        fig_nap = go.Figure(data=nap_data)
        fig_nap.update_layout(
            title=f"{patient} —— 日间小睡时间",
            xaxis_title="日期",
            yaxis_title="时间",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=500
        )
        st.plotly_chart(fig_nap, use_container_width=True)

        # 3. 入睡所需时长
        fig2 = px.line(df, x="date_fmt", y="sleep_latency",
                       markers=True, title=f"{patient} —— 入睡所需时长（分钟）")
        st.plotly_chart(fig2, use_container_width=True)

        # 4. 夜间觉醒次数
        fig3 = px.line(df, x="date_fmt", y="night_awake_count",
                       markers=True, title=f"{patient} —— 夜间觉醒次数")
        st.plotly_chart(fig3, use_container_width=True)

        # 5. 夜间觉醒总时长
        fig4 = px.line(df, x="date_fmt", y="night_awake_total",
                       markers=True, title=f"{patient} —— 夜间觉醒总时长（分钟）")
        st.plotly_chart(fig4, use_container_width=True)

        # 6. 总睡眠时长
        fig5 = px.line(df, x="date_fmt", y="total_sleep_hours",
                       markers=True, title=f"{patient} —— 总睡眠时长（小时）")
        st.plotly_chart(fig5, use_container_width=True)

        st.subheader("原始数据")
        st.dataframe(df.reset_index(drop=True))

# 新增的按日期查询所有记录功能
with tab3:
    st.subheader("按日期查询所有记录")
    query_date = st.date_input("选择查询日期", date.today())
    
    if st.button("查询该日期所有记录"):
        # 查询指定日期的所有记录
        df_all = run_query(
            "SELECT * FROM sleep_diary WHERE entry_date=%s ORDER BY name, created_at DESC",
            params=(query_date.isoformat(),)
        )
        
        if df_all.empty:
            st.warning(f"{query_date} 没有找到任何记录")
        else:
            st.success(f"找到 {len(df_all)} 条记录（{query_date}）")
            
            # 按患者分组显示
            patients = df_all["name"].unique()
            for patient in patients:
                st.subheader(f"患者: {patient}")
                patient_df = df_all[df_all["name"] == patient]
                st.dataframe(patient_df)
            
            # 显示完整数据表
            st.subheader("完整数据表")
            st.dataframe(df_all)
