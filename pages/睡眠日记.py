import streamlit as st
import pymysql, os
from datetime import date

st.set_page_config(page_title="睡眠日记", layout="centered")
st.title("🛏️ 国际标准睡眠日记（核心版）")

with st.form("sleep_diary"):
    st.subheader("🌅 早晨填写（起床后1小时内完成）")
    name = st.text_input("姓名")
    record_date = st.date_input("日期", date.today())

    # 昨日白天
    daytime_nap = st.text_input("昨日白天小睡（例：14:00-14:20，共20分钟）", value="无")
    caffeine = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value="无")
    alcohol = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value="无")
    medication = st.text_input("昨晚药物使用（例：唑吡坦，10mg，22:00）", value="无")
    daytime_mood = st.slider("昨日日间情绪状态（1-5分）", 1, 5, 3)
    sleep_interference = ";".join(
        st.multiselect("昨晚干扰睡眠因素", ["噪音", "疼痛", "压力", "温度", "光线", "其他"])
    )

    # 昨晚睡眠
    bed_time = st.text_input("昨晚上床时间（HH:MM）", "23:00")
    try_sleep_time = st.text_input("试图入睡时间（HH:MM）", "23:15")
    sleep_latency = st.number_input("入睡所需时间（分钟）", 0, 120, 30)
    night_awake_count = st.number_input("夜间觉醒次数", 0, 10, 0)
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, 0)
    final_wake_time = st.text_input("早晨最终醒来时间（HH:MM）", "6:30")
    get_up_time = st.text_input("起床时间（HH:MM）", "6:40")
    total_sleep_hours = st.number_input("总睡眠时间（小时）", 0.0, 24.0, 7.0, 0.1)
    sleep_quality = st.slider("睡眠质量评分（1-5分）", 1, 5, 4)
    morning_feeling = st.slider("晨起后感觉（1-3分）", 1, 3, 2)

    submitted = st.form_submit_button("保存日记")

if submitted and name.strip():
    record = {
        "name": name,
        "record_date": record_date.isoformat(),
        "daytime_nap": daytime_nap,
        "caffeine": caffeine,
        "alcohol": alcohol,
        "medication": medication,
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

    conn = pymysql.connect(
        host=os.getenv("SQLPUB_HOST"),
        port=int(os.getenv("SQLPUB_PORT", 3307)),
        user=os.getenv("SQLPUB_USER"),
        password=os.getenv("SQLPUB_PWD"),
        database=os.getenv("SQLPUB_DB"),
        charset="utf8mb4"
    )
    sql = """
    INSERT INTO sleep_diary
    (name, record_date, daytime_nap, caffeine, alcohol, medication,
     daytime_mood, sleep_interference, bed_time, try_sleep_time,
     sleep_latency, night_awake_count, night_awake_total,
     final_wake_time, get_up_time, total_sleep_hours,
     sleep_quality, morning_feeling)
    VALUES
    (%(name)s, %(record_date)s, %(daytime_nap)s, %(caffeine)s, %(alcohol)s, %(medication)s,
     %(daytime_mood)s, %(sleep_interference)s, %(bed_time)s, %(try_sleep_time)s,
     %(sleep_latency)s, %(night_awake_count)s, %(night_awake_total)s,
     %(final_wake_time)s, %(get_up_time)s, %(total_sleep_hours)s,
     %(sleep_quality)s, %(morning_feeling)s)
    """
    conn.cursor().execute(sql, record)
    conn.commit()
    conn.close()
    st.success("睡眠日记已保存！")

else:
    st.warning("请填写姓名后再保存")
