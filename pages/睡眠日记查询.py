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

# 时间 → 分钟（跨天）
def time_to_min(t):
    try:
        h, m = map(int, t.split(":"))
        return (h if h >= 12 else h + 24) * 60 + m
    except:
        return None

# 分钟 → 时间字符串
def min_to_time(m):
    h, mi = divmod(int(m), 60)
    h = h - 24 if h >= 24 else h
    return f"{h:02d}:{mi:02d}"

# 中英文字段映射字典
field_mapping = {
    "name": "姓名",
    "record_date": "记录日期",
    "entry_date": "填写日期",
    "nap_start": "日间小睡开始时间",
    "nap_end": "日间小睡结束时间",
    "daytime_bed_minutes": "日间卧床时间（分钟）",
    "caffeine": "咖啡因摄入",
    "alcohol": "酒精摄入",
    "med_name": "药物名称",
    "med_dose": "药物剂量",
    "med_time": "服药时间",
    "daytime_mood": "日间情绪状态",
    "sleep_interference": "睡眠干扰因素",
    "bed_time": "上床时间",
    "try_sleep_time": "试图入睡时间",
    "sleep_latency": "入睡所需时间（分钟）",
    "night_awake_count": "夜间觉醒次数",
    "night_awake_total": "夜间觉醒总时长（分钟）",
    "final_wake_time": "早晨最终醒来时间",
    "get_up_time": "起床时间",
    "total_sleep_hours": "总睡眠时长（小时）",
    "sleep_quality": "睡眠质量自我评价",
    "morning_feeling": "晨起后精神状态",
    "created_at": "创建时间"
}

# ---------- 单次查询 ----------
with tab1:
    patient = st.text_input("患者姓名").strip()
    entry_date = st.date_input("填写日期", date.today())
    if st.button("查询单次") and patient:
        df = run_query(
            "SELECT * FROM sleep_diary WHERE name=%s AND entry_date=%s ORDER BY created_at DESC",
            params=(patient, entry_date.isoformat())
        )
        
        if df.empty:
            st.warning("暂无记录")
        else:
            # 将列名替换为中文
            df_display = df.copy()
            df_display.columns = [field_mapping.get(col, col) for col in df_display.columns]
            
            # 重新排列列的顺序，将重要的信息放在前面
            important_cols = [
                "姓名",
                "记录日期",
                "填写日期",
                "上床时间",
                "试图入睡时间",
                "入睡所需时间（分钟）",
                "夜间觉醒次数",
                "夜间觉醒总时长（分钟）",
                "早晨最终醒来时间",
                "起床时间",
                "总睡眠时长（小时）",
                "睡眠质量自我评价",
                "晨起后精神状态",
                "日间小睡开始时间",
                "日间小睡结束时间",
                "日间卧床时间（分钟）",
                "日间情绪状态",
                "睡眠干扰因素",
                "咖啡因摄入",
                "酒精摄入",
                "药物名称",
                "药物剂量",
                "服药时间",
                "创建时间"
            ]
            
            # 只保留存在的列
            existing_cols = [col for col in important_cols if col in df_display.columns]
            # 添加其他可能的列
            other_cols = [col for col in df_display.columns if col not in existing_cols]
            final_cols = existing_cols + other_cols
            
            df_display = df_display[final_cols]
            
            # 显示数据框
            st.dataframe(df_display, use_container_width=True)
            
            # 为每条记录创建详细查看
            for idx, row in df.iterrows():
                with st.expander(f"记录详情 - 日期: {row['record_date']} (填写时间: {row['entry_date']}, 创建时间: {row['created_at']})"):
                    col1, col2 = st.columns(2)
                    
                    # 左列显示夜间睡眠信息
                    with col1:
                        st.markdown("**🌙 夜间睡眠记录**")
                        st.write(f"**上床时间:** {row['bed_time']}")
                        st.write(f"**试图入睡时间:** {row['try_sleep_time']}")
                        st.write(f"**入睡所需时间:** {row['sleep_latency']} 分钟")
                        st.write(f"**夜间觉醒次数:** {row['night_awake_count']} 次")
                        st.write(f"**夜间觉醒总时长:** {row['night_awake_total']} 分钟")
                        st.write(f"**早晨最终醒来时间:** {row['final_wake_time']}")
                        st.write(f"**起床时间:** {row['get_up_time']}")
                        st.write(f"**总睡眠时长:** {row['total_sleep_hours']:.2f} 小时")
                        st.write(f"**睡眠质量自我评价:** {row['sleep_quality']}")
                        st.write(f"**晨起后精神状态:** {row['morning_feeling']}")
                    
                    # 右列显示日间活动信息
                    with col2:
                        st.markdown("**☀️ 日间活动记录**")
                        st.write(f"**日间小睡开始时间:** {row['nap_start']}")
                        st.write(f"**日间小睡结束时间:** {row['nap_end']}")
                        st.write(f"**日间卧床时间:** {row['daytime_bed_minutes']} 分钟")
                        st.write(f"**日间情绪状态:** {row['daytime_mood']}")
                        st.write(f"**咖啡因摄入:** {row['caffeine']}")
                        st.write(f"**酒精摄入:** {row['alcohol']}")
                        
                        if pd.notna(row['med_name']) and row['med_name'].strip():
                            st.write(f"**药物名称:** {row['med_name']}")
                            st.write(f"**药物剂量:** {row['med_dose']}")
                            st.write(f"**服药时间:** {row['med_time']}")
                        
                        st.write(f"**睡眠干扰因素:** {row['sleep_interference']}")

# ---------- 最近7次汇总 ----------
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

        # 1. 夜间关键时间
        night_cols = ["bed_time", "try_sleep_time", "final_wake_time", "get_up_time"]
        night_labels = ["上床时间", "试图入睡时间", "最终醒来时间", "起床时间"]
        data1 = []
        for col, label in zip(night_cols, night_labels):
            mins = df[col].apply(time_to_min)
            data1.append(go.Scatter(x=df["date_fmt"], y=mins, name=label,
                                    mode="lines+markers+text", text=df[col],
                                    textposition="top center"))
        fig1 = go.Figure(data1)
        fig1.update_layout(
            title="夜间关键时间点",
            yaxis=dict(
                tickformat="%H:%M", 
                autorange=True,
                showticklabels=False  # 隐藏y轴数字
            ),
            legend=dict(
                orientation="h",        # 水平排列
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        st.plotly_chart(fig1, use_container_width=True)

        # 2. 日间小睡时间
        nap_cols = ["nap_start", "nap_end"]
        nap_labels = ["小睡开始时间", "小睡结束时间"]
        data2 = []
        for col, label in zip(nap_cols, nap_labels):
            mins = df[col].apply(lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))
            data2.append(go.Scatter(x=df["date_fmt"], y=mins, name=label,
                                    mode="lines+markers+text", text=df[col],
                                    textposition="top center"))
        fig2 = go.Figure(data2)
        fig2.update_layout(
            title="日间小睡时间",
            yaxis=dict(
                tickformat="%H:%M", 
                autorange=True,
                showticklabels=False  # 隐藏y轴数字
            ),
            legend=dict(
                orientation="h",        # 永平排列
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        st.plotly_chart(fig2, use_container_width=True)

        # 3-7 其余指标
        metrics = [("sleep_latency", "入睡所需时长（分钟）"),
                   ("night_awake_count", "夜间觉醒次数"),
                   ("night_awake_total", "夜间觉醒总时长（分钟）"),
                   ("total_sleep_hours", "总睡眠时长（小时）")]
        for col, title in metrics:
            fig = px.line(df, x="date_fmt", y=col, markers=True, title=title)
            st.plotly_chart(fig, use_container_width=True)

        # 显示汇总数据框（使用中文列名）
        df_display = df.copy()
        df_display.columns = [field_mapping.get(col, col) for col in df_display.columns]
        
        important_cols = [
            "姓名",
            "记录日期",
            "填写日期",
            "上床时间",
            "试图入睡时间",
            "入睡所需时间（分钟）",
            "夜间觉醒次数",
            "夜间觉醒总时长（分钟）",
            "早晨最终醒来时间",
            "起床时间",
            "总睡眠时长（小时）",
            "睡眠质量自我评价",
            "晨起后精神状态",
            "日间小睡开始时间",
            "日间小睡结束时间",
            "日间卧床时间（分钟）",
            "日间情绪状态",
            "睡眠干扰因素",
            "咖啡因摄入",
            "酒精摄入",
            "药物名称",
            "药物剂量",
            "服药时间",
            "创建时间"
        ]
        
        existing_cols = [col for col in important_cols if col in df_display.columns]
        other_cols = [col for col in df_display.columns if col not in existing_cols]
        final_cols = existing_cols + other_cols
        
        df_display = df_display[final_cols]
        
        st.dataframe(df_display.reset_index(drop=True))

# ---------- 按日期查询 ----------
with tab3:
    query_date = st.date_input("选择查询日期", date.today())
    if st.button("查询该日期所有记录"):
        df_all = run_query(
            "SELECT * FROM sleep_diary WHERE entry_date=%s ORDER BY name, created_at DESC",
            params=(query_date.isoformat())
        )
        if df_all.empty:
            st.warning(f"{query_date} 没有发现记录")
        else:
            st.success(f"共 {len(df_all)} 条记录")
            
            # 将列名替换为中文
            df_display = df_all.copy()
            df_display.columns = [field_mapping.get(col, col) for col in df_display.columns]
            
            # 重新排列列的顺序
            important_cols = [
                "姓名",
                "记录日期",
                "填写日期",
                "上床时间",
                "试图入睡时间",
                "入睡所需时间（分钟）",
                "夜间觉醒次数",
                "夜间觉醒总时长（分钟）",
                "早晨最终醒来时间",
                "起床时间",
                "总睡眠时长（小时）",
                "睡眠质量自我评价",
                "晨起后精神状态",
                "日间小睡开始时间",
                "日间小睡结束时间",
                "日间卧床时间（分钟）",
                "日间情绪状态",
                "睡眠干扰因素",
                "咖啡因摄入",
                "酒精摄入",
                "药物名称",
                "药物剂量",
                "服药时间",
                "创建时间"
            ]
            
            existing_cols = [col for col in important_cols if col in df_display.columns]
            other_cols = [col for col in df_display.columns if col not in existing_cols]
            final_cols = existing_cols + other_cols
            
            df_display = df_display[final_cols]
            
            st.dataframe(df_display, use_container_width=True)
