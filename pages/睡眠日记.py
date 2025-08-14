import streamlit as st
import pymysql
import os
from datetime import date

st.set_page_config(page_title="睡眠日记", layout="centered")
st.title("🛏️ 国际标准睡眠日记（核心版）")

# 创建时间选项（每15分钟一个选项，减少数量）
def generate_time_slots(start_hour, end_hour):
    slots = []
    for h in range(start_hour, end_hour + 1):
        hour = h % 24
        for m in [0, 15, 30, 45]:
            slots.append(f"{hour:02d}:{m:02d}")
    return slots

# 生成时间选项
daytime_slots = generate_time_slots(6, 20)  # 白天时间：06:00-20:00
evening_slots = generate_time_slots(20, 26)  # 晚上时间：20:00-02:00（26=02:00+24）
morning_slots = generate_time_slots(2, 12)   # 早晨时间：02:00-12:00

# 确保默认值在选项中
if "14:00" not in daytime_slots: daytime_slots.append("14:00")
if "14:15" not in daytime_slots: daytime_slots.append("14:15")  # 添加备用值
if "06:30" not in morning_slots: morning_slots.append("06:30")
if "06:45" not in morning_slots: morning_slots.append("06:45")  # 添加备用值
if "23:00" not in evening_slots: evening_slots.append("23:00")
if "22:00" not in evening_slots: evening_slots.append("22:00")

# 创建表单
with st.form("sleep_diary"):
    name = st.text_input("姓名", placeholder="请输入您的姓名")
    record_date = st.date_input("记录日期", date.today())
    
    st.subheader("日间活动记录")
    col1, col2 = st.columns(2)
    nap_start = col1.select_slider("昨日白天小睡开始时间", options=daytime_slots, value="14:00")
    nap_end = col2.select_slider("昨日白天小睡结束时间", options=daytime_slots, value="14:15")
    
    caffeine = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value="无")
    alcohol = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value="无")
    
    st.subheader("药物使用")
    med_col1, med_col2, med_col3 = st.columns(3)
    med_name = med_col1.text_input("药物名称", placeholder="无")
    med_dose = med_col2.text_input("剂量", placeholder="0mg")
    med_time = med_col3.select_slider("服用时间", options=evening_slots, value="22:00")
    
    daytime_mood = st.radio("昨日日间情绪状态", ["很差", "差", "一般", "好", "很好"], horizontal=True, index=2)
    
    sleep_interference = ";".join(
        st.multiselect("昨晚干扰睡眠因素（可多选）", ["噪音", "疼痛", "压力", "温度", "光线", "其他"])
    )
    
    st.subheader("夜间睡眠记录")
    bed_time = st.select_slider("昨晚上床时间", options=evening_slots, value="23:00")
    try_sleep_time = st.select_slider("试图入睡时间", options=evening_slots, value="23:15")
    
    col3, col4 = st.columns(2)
    sleep_latency = col3.number_input("入睡所需时间（分钟）", 0, 180, 30)
    night_awake_count = col4.number_input("夜间觉醒次数", 0, 15, 0)
    
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, 0)
    
    st.subheader("晨间记录")
    col5, col6 = st.columns(2)
    final_wake_time = col5.select_slider("早晨最终醒来时间", options=morning_slots, value="06:30")
    get_up_time = col6.select_slider("起床时间", options=morning_slots, value="06:45")
    
    total_sleep_hours = st.number_input("总睡眠时间（小时）", 0.0, 24.0, 7.0, 0.1)
    
    sleep_quality = st.radio("睡眠质量评分", ["很差", "差", "一般", "好", "很好"], horizontal=True, index=2)
    morning_feeling = st.radio("晨起后感觉", ["差", "一般", "好"], horizontal=True, index=1)
    
    # 确保提交按钮在表单内部
    submitted = st.form_submit_button("保存日记")

# 数据库连接和保存逻辑
if submitted:
    if not name.strip():
        st.error("请填写姓名后再保存")
    else:
        try:
            record = {
                "name": name,
                "record_date": record_date.isoformat(),
                "nap_start": nap_start,
                "nap_end": nap_end,
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
            (name, record_date, nap_start, nap_end, caffeine, alcohol, med_name, med_dose, med_time,
             daytime_mood, sleep_interference, bed_time, try_sleep_time,
             sleep_latency, night_awake_count, night_awake_total,
             final_wake_time, get_up_time, total_sleep_hours,
             sleep_quality, morning_feeling)
            VALUES
            (%(name)s, %(record_date)s, %(nap_start)s, %(nap_end)s, %(caffeine)s, %(alcohol)s,
             %(med_name)s, %(med_dose)s, %(med_time)s, %(daytime_mood)s, %(sleep_interference)s,
             %(bed_time)s, %(try_sleep_time)s, %(sleep_latency)s, %(night_awake_count)s,
             %(night_awake_total)s, %(final_wake_time)s, %(get_up_time)s,
             %(total_sleep_hours)s, %(sleep_quality)s, %(morning_feeling)s)
            """
            
            with conn.cursor() as cursor:
                cursor.execute(sql, record)
                conn.commit()
            
            st.success(f"{record_date} 睡眠日记已成功保存！")
        except Exception as e:
            st.error(f"保存失败: {str(e)}")
        finally:
            if conn:
                conn.close()
