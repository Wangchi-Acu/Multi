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

# 时间转换函数（支持跨天时间）
def time_to_min(t):
    try:
        h, m = map(int, t.split(":"))
        # 处理跨天时间（如02:00表示为26:00）
        if h < 12:  # 早晨时间（02:00-12:00）加24小时
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
        # 获取指定日期的最新记录
        df = run_query(
            "SELECT * FROM sleep_diary WHERE name=%s AND record_date=%s ORDER BY created_at DESC LIMIT 1",
            params=(patient, record_date.isoformat())
        )
        st.dataframe(df.T if not df.empty else "暂无记录")

with tab2:
    patient = st.text_input("患者姓名（汇总）").strip()
    if st.button("查询最近7次") and patient:
        # 获取最近7个不同日期的最新记录
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
            ORDER BY t1.record_date DESC
            """,
            params=(patient,)
        )
        
        if df.empty:
            st.warning("暂无记录")
            st.stop()

        # 按日期排序（从旧到新）
        df = df.sort_values("record_date")
        df["date_fmt"] = pd.to_datetime(df["record_date"]).dt.strftime("%m-%d")

        # ----- 第一张图：夜间关键时间 -----
        night_time_cols = ["bed_time", "try_sleep_time", "final_wake_time", "get_up_time", "med_time"]
        night_time_labels = ["上床时间", "试图入睡时间", "最终醒来时间", "起床时间", "服药时间"]
        
        # 准备数据
        night_data = []
        for col, label in zip(night_time_cols, night_time_labels):
            # 转换为分钟数
            minutes = df[col].apply(time_to_min)
            
            # 计算每个点的值（用于显示标签）
            values = []
            for m in minutes:
                if pd.isna(m):
                    values.append("")
                else:
                    # 转换为原始时间格式显示
                    h, m_val = divmod(m, 60)
                    if h >= 24:  # 处理跨天时间
                        h -= 24
                    values.append(f"{int(h):02d}:{int(m_val):02d}")
            
            night_data.append(go.Scatter(
                x=df["date_fmt"],
                y=minutes,
                name=label,
                mode='lines+markers+text',
                text=values,
                textposition="top center",
                marker=dict(size=10),
                line=dict(width=3),
                textfont=dict(size=12, color='black')
            ))
        
        # 创建图表
        fig_night = go.Figure(data=night_data)
        
        # 设置布局
        fig_night.update_layout(
            title=f"{patient} —— 夜间关键时间点",
            xaxis_title="日期",
            yaxis_title="时间",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=500
        )
        
        # 设置Y轴格式（分钟数转时间）
        min_y = min([min(df[col].apply(time_to_min).min() for col in night_time_cols])
        max_y = max([max(df[col].apply(time_to_min).max() for col in night_time_cols])
        
        # 创建刻度值（每30分钟一个刻度）
        y_ticks = list(range(int(min_y) - 30, int(max_y) + 30, 30))
        y_ticktext = [min_to_time(t) for t in y_ticks]
        
        fig_night.update_yaxes(
            tickvals=y_ticks,
            ticktext=y_ticktext,
            tickangle=0
        )
        
        # 显示图表
        st.plotly_chart(fig_night, use_container_width=True)
        
        # ----- 第二张图：日间小睡时间 -----
        nap_cols = ["nap_start", "nap_end"]
        nap_labels = ["小睡开始时间", "小睡结束时间"]
        
        # 准备数据
        nap_data = []
        for col, label in zip(nap_cols, nap_labels):
            # 转换为分钟数（日间时间不需要特殊处理）
            minutes = df[col].apply(lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))
            
            # 计算每个点的值（用于显示标签）
            values = df[col].tolist()
            
            nap_data.append(go.Scatter(
                x=df["date_fmt"],
                y=minutes,
                name=label,
                mode='lines+markers+text',
                text=values,
                textposition="top center",
                marker=dict(size=10),
                line=dict(width=3),
                textfont=dict(size=12, color='black')
            ))
        
        # 创建图表
        fig_nap = go.Figure(data=nap_data)
        
        # 设置布局
        fig_nap.update_layout(
            title=f"{patient} —— 日间小睡时间",
            xaxis_title="日期",
            yaxis_title="时间",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=500
        )
        
        # 设置Y轴格式（分钟数转时间）
        min_y = min([min(df[col].apply(lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1])) for col in nap_cols])
        max_y = max([max(df[col].apply(lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1])) for col in nap_cols])
        
        # 创建刻度值（每30分钟一个刻度）
        y_ticks = list(range(int(min_y) - 30, int(max_y) + 30, 30))
        y_ticktext = [min_to_time(t) for t in y_ticks]
        
        fig_nap.update_yaxes(
            tickvals=y_ticks,
            ticktext=y_ticktext,
            tickangle=0
        )
        
        # 显示图表
        st.plotly_chart(fig_nap, use_container_width=True)
        
        # ----- 其他睡眠指标图表 -----
        # 1. 入睡所需时长
        fig2 = px.line(df, x="date_fmt", y="sleep_latency",
                       markers=True, 
                       title=f"{patient} —— 入睡所需时长（分钟）",
                       text="sleep_latency")
        fig2.update_traces(
            marker=dict(size=10),
            line=dict(width=3),
            textposition="top center",
            textfont=dict(size=12, color='black')
        )
        fig2.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # 2. 夜间觉醒次数
        fig3 = px.line(df, x="date_fmt", y="night_awake_count",
                       markers=True, 
                       title=f"{patient} —— 夜间觉醒次数",
                       text="night_awake_count")
        fig3.update_traces(
            marker=dict(size=10),
            line=dict(width=3),
            textposition="top center",
            textfont=dict(size=12, color='black')
        )
        fig3.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=400
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # 3. 夜间觉醒总时长
        fig4 = px.line(df, x="date_fmt", y="night_awake_total",
                       markers=True, 
                       title=f"{patient} —— 夜间觉醒总时长（分钟）",
                       text="night_awake_total")
        fig4.update_traces(
            marker=dict(size=10),
            line=dict(width=3),
            textposition="top center",
            textfont=dict(size=12, color='black')
        )
        fig4.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=400
        )
        st.plotly_chart(fig4, use_container_width=True)
        
        # 4. 总睡眠时长
        fig5 = px.line(df, x="date_fmt", y="total_sleep_hours",
                       markers=True, 
                       title=f"{patient} —— 总睡眠时长（小时）",
                       text=df["total_sleep_hours"].apply(lambda x: f"{x:.2f}"))
        fig5.update_traces(
            marker=dict(size=10),
            line=dict(width=3),
            textposition="top center",
            textfont=dict(size=12, color='black')
        )
        fig5.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            font=dict(family="Microsoft YaHei", size=14),
            height=400
        )
        st.plotly_chart(fig5, use_container_width=True)
        
        # 5. 日间卧床时间
        if "daytime_bed_minutes" in df.columns:
            fig6 = px.line(df, x="date_fmt", y="daytime_bed_minutes",
                           markers=True, 
                           title=f"{patient} —— 日间卧床时间（分钟）",
                           text="daytime_bed_minutes")
            fig6.update_traces(
                marker=dict(size=10),
                line=dict(width=3),
                textposition="top center",
                textfont=dict(size=12, color='black')
            )
            fig6.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                font=dict(family="Microsoft YaHei", size=14),
                height=400
            )
            st.plotly_chart(fig6, use_container_width=True)

        # 原始数据表
        st.subheader("原始数据")
        st.dataframe(df.reset_index(drop=True))
