import streamlit as st
import pymysql
import os
from datetime import date, timedelta
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 自定义CSS样式（保持不变）
st.markdown("""
<style>
/* 原有样式保持不变 */
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="睡眠日记", layout="centered")
st.image("jsszyylogo.png", width=500)
st.markdown("""
<div style='color: #000000; padding: 2px; border-radius: 15px; text-align: left;'>
    <h1 style='font-size: 37px; margin: 0; font-weight: 700;'>江苏省中医院针灸科</h1>
    <h1 style='font-size: 32px; margin: -15px 0 0 0; font-weight: 600;'>失眠专病门诊</h1>
</div>
""", unsafe_allow_html=True)
st.title("🛏️ 睡眠日记")

# 数据库连接函数
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

# 生成时间选项
def generate_time_slots(start_hour, end_hour):
    slots = []
    for h in range(start_hour, end_hour + 1):
        hour = h % 24
        for m in range(0, 60, 5):
            slots.append(f"{hour:02d}:{m:02d}")
    return slots

# 绘图函数 - 最近7次汇总图表
def plot_recent_7_days(patient_name):
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
        params=(patient_name,)
    )
    if df.empty:
        st.warning("暂无记录")
        return

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
            showticklabels=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
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
            showticklabels=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
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

    st.dataframe(df.reset_index(drop=True))

# 生成时间选项
daytime_slots = generate_time_slots(6, 20)  # 白天时间：06:00-20:00
evening_slots = generate_time_slots(20, 26)  # 晚上时间：20:00-02:00（26=02:00+24）
morning_slots = generate_time_slots(2, 12)   # 早晨时间：02:00-12:00

# 日期处理
today = date.today()
yesterday = today - timedelta(days=1)

# 创建表单
with st.form("sleep_diary"):
    # 姓名和日期部分
    name = st.text_input("姓名", placeholder="请输入您的姓名")
    
    col_date1, col_date2 = st.columns(2)
    # 记录日期（日记内容对应的日期，默认为昨天）
    record_date = col_date1.date_input("记录日期（睡眠日期）", yesterday)
    
    # 填写日期（提交日记的日期，默认为今天，不可更改）
    with col_date2:
        st.markdown('<div class="readonly-date">', unsafe_allow_html=True)
        entry_date = st.date_input("填写日期", today, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("日间活动记录")
    col1, col2 = st.columns(2)
    nap_start = col1.select_slider("昨日白天小睡开始时间", options=daytime_slots, value="14:00")
    nap_end = col2.select_slider("昨日白天小睡结束时间", options=daytime_slots, value="14:05")
    
    # 添加日间卧床时间（单位：分钟）
    daytime_bed_minutes = st.number_input(
        "日间卧床时间（分钟）",
        min_value=0,
        max_value=600,
        value=0,
        step=5,
        help="除小睡外，日间在床上休息但未入睡的时间"
    )
    
    caffeine = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value="无")
    alcohol = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value="无")
    
    st.subheader("药物使用")
    med_col1, med_col2, med_col3 = st.columns(3)
    med_name = med_col1.text_input("药物名称", placeholder="无")
    med_dose = med_col2.text_input("剂量", placeholder="0mg")
    med_time = med_col3.select_slider("服用时间", options=evening_slots, value="22:00")
    
    # 日间情绪状态
    daytime_mood = st.radio("昨日日间情绪状态", ["优", "良", "中", "差", "很差"], horizontal=True, index=2)
    
    # 干扰睡眠因素 - 添加"无"选项并设为默认
    interference_options = ["噪音", "疼痛", "压力", "温度", "光线", "其他", "无"]
    selected_interference = st.multiselect("昨晚干扰睡眠因素（可多选）", 
                                          interference_options, 
                                          default=["无"])
    
    # 如果用户选择了"无"和其他选项，则只保留"无"
    if "无" in selected_interference:
        sleep_interference = "无"
    elif not selected_interference:
        sleep_interference = "无"
    else:
        sleep_interference = ";".join(selected_interference)
    
    st.subheader("夜间睡眠记录")
    bed_time = st.select_slider("昨晚上床时间", options=evening_slots, value="23:00")
    try_sleep_time = st.select_slider("试图入睡时间", options=evening_slots, value="23:05")
    
    col3, col4 = st.columns(2)
    sleep_latency = col3.number_input("入睡所需时间（分钟）", 0, 800, 30)
    night_awake_count = col4.number_input("夜间觉醒次数", 0, 15, 0)
    
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, 0)

    col5, col6 = st.columns(2)
    final_wake_time = col5.select_slider("早晨最终醒来时间", options=morning_slots, value="06:30")
    get_up_time = col6.select_slider("起床时间", options=morning_slots, value="06:35")
    
    # 总睡眠时间 - 改为小时和分钟两个竖向滑动选择
    st.markdown('<div class="vertical-sliders">', unsafe_allow_html=True)
    st.markdown("**总睡眠时间**")
    
    col_sleep1, col_sleep2 = st.columns(2)
    with col_sleep1:
        sleep_hours = st.slider("小时", 0, 12, 7, format="%d小时", key="sleep_hours")
    with col_sleep2:
        sleep_minutes = st.slider("分钟", 0, 55, 0, step=5, format="%d分钟", key="sleep_minutes")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    total_sleep_hours = sleep_hours + (sleep_minutes / 60.0)
    
    # 睡眠质量自我评价
    sleep_quality = st.radio("睡眠质量自我评价", ["优", "良", "中", "差", "很差"], horizontal=True, index=2)
    
    # 晨起后精神状态 - 改为好、中、差
    morning_feeling_options = ["好", "中", "差"]
    morning_feeling = st.radio("晨起后精神状态", morning_feeling_options, horizontal=True, 
                              index=1)  # 默认选中"中"
    
    # 提交按钮
    submitted = st.form_submit_button("保存日记")

# 数据库连接和保存逻辑
if submitted:
    if not name.strip():
        st.error("请填写姓名后再保存")
    else:
        try:
            # 构建记录数据
            record = {
                "name": name,
                "record_date": record_date.isoformat(),  # 睡眠日期
                "entry_date": entry_date.isoformat(),    # 填写日期
                "nap_start": nap_start,
                "nap_end": nap_end,
                "daytime_bed_minutes": daytime_bed_minutes,  # 新增的日间卧床时间
                "caffeine": caffeine,
                "alcohol": alcohol,
                "med_name": med_name,
                "med_dose": med_dose,
                "med_time": med_time,
                "daytime_mood": daytime_mood,
                "sleep_interference": sleep_interference,
                "bed_time": bed_time,
                "try_sleep_time": try_sleep_time,
                "sleep_latency": sleep_latency,
                "night_awake_count": night_awake_count,
                "night_awake_total": night_awake_total,
                "final_wake_time": final_wake_time,
                "get_up_time": get_up_time,
                "total_sleep_hours": total_sleep_hours,
                "sleep_quality": sleep_quality,
                "morning_feeling": morning_feeling
            }

            # 显示加载提示
            with st.spinner("日记正在保存，请勿离开！"):
                # 连接数据库
                conn = pymysql.connect(
                    host=os.getenv("SQLPUB_HOST"),
                    port=int(os.getenv("SQLPUB_PORT", 3307)),
                    user=os.getenv("SQLPUB_USER"),
                    password=os.getenv("SQLPUB_PWD"),
                    database=os.getenv("SQLPUB_DB"),
                    charset="utf8mb4"
                )
                
                with conn.cursor() as cursor:
                    # 检查是否已存在该用户同一天的记录
                    check_sql = """
                    SELECT COUNT(*) FROM sleep_diary 
                    WHERE name = %(name)s AND record_date = %(record_date)s
                    """
                    cursor.execute(check_sql, {"name": name, "record_date": record_date.isoformat()})
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # 更新现有记录
                        update_sql = """
                        UPDATE sleep_diary
                        SET entry_date = %(entry_date)s,
                            nap_start = %(nap_start)s,
                            nap_end = %(nap_end)s,
                            daytime_bed_minutes = %(daytime_bed_minutes)s,
                            caffeine = %(caffeine)s,
                            alcohol = %(alcohol)s,
                            med_name = %(med_name)s,
                            med_dose = %(med_dose)s,
                            med_time = %(med_time)s,
                            daytime_mood = %(daytime_mood)s,
                            sleep_interference = %(sleep_interference)s,
                            bed_time = %(bed_time)s,
                            try_sleep_time = %(try_sleep_time)s,
                            sleep_latency = %(sleep_latency)s,
                            night_awake_count = %(night_awake_count)s,
                            night_awake_total = %(night_awake_total)s,
                            final_wake_time = %(final_wake_time)s,
                            get_up_time = %(get_up_time)s,
                            total_sleep_hours = %(total_sleep_hours)s,
                            sleep_quality = %(sleep_quality)s,
                            morning_feeling = %(morning_feeling)s
                        WHERE name = %(name)s AND record_date = %(record_date)s
                        """
                        cursor.execute(update_sql, record)
                        action = "更新"
                    else:
                        # 插入新记录
                        insert_sql = """
                        INSERT INTO sleep_diary
                        (name, record_date, entry_date, nap_start, nap_end, daytime_bed_minutes, caffeine, alcohol, 
                         med_name, med_dose, med_time, daytime_mood, sleep_interference, 
                         bed_time, try_sleep_time, sleep_latency, night_awake_count, 
                         night_awake_total, final_wake_time, get_up_time, total_sleep_hours,
                         sleep_quality, morning_feeling)
                        VALUES
                        (%(name)s, %(record_date)s, %(entry_date)s, %(nap_start)s, %(nap_end)s, 
                         %(daytime_bed_minutes)s, %(caffeine)s, %(alcohol)s, %(med_name)s, %(med_dose)s, %(med_time)s, 
                         %(daytime_mood)s, %(sleep_interference)s, %(bed_time)s, %(try_sleep_time)s, 
                         %(sleep_latency)s, %(night_awake_count)s, %(night_awake_total)s, 
                         %(final_wake_time)s, %(get_up_time)s, %(total_sleep_hours)s, 
                         %(sleep_quality)s, %(morning_feeling)s)
                        """
                        cursor.execute(insert_sql, record)
                        action = "保存"
                
                conn.commit()
                conn.close()
            
            # 显示成功消息
            st.success("日记保存完成！")
            
            # 展示最近7次汇总图表
            st.subheader("📊 您最近7天的睡眠情况")
            plot_recent_7_days(name)
                
        except Exception as e:
            st.error(f"操作失败: {str(e)}")
