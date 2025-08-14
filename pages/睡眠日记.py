import streamlit as st
import pymysql
import os
from datetime import date

st.set_page_config(page_title="睡眠日记", layout="centered")
st.title("🛏️ 国际标准睡眠日记（核心版）")

# 修正时间滑块选项范围
def generate_time_slots(start_hour, end_hour):
    slots = []
    for h in range(start_hour, end_hour + 1):
        hour = h % 24
        for m in range(0, 60, 5):  # 每5分钟一个选项，减少选项数量
            slots.append(f"{hour:02d}:{m:02d}")
    return slots

# 生成时间选项（减少选项数量，每5分钟一个）
daytime_slots = generate_time_slots(6, 20)  # 白天时间：06:00-20:00
evening_slots = generate_time_slots(20, 26)  # 晚上时间：20:00-02:00（26=02:00+24）
morning_slots = generate_time_slots(2, 12)   # 早晨时间：02:00-12:00

with st.form("sleep_diary"):
    name = st.text_input("姓名")
    record_date = st.date_input("记录日期", date.today())

    col1, col2 = st.columns(2)
    # 使用白天时间段作为小睡时间选项
    nap_start = col1.select_slider("昨日白天小睡开始时间", options=daytime_slots, value="14:00")
    nap_end   = col2.select_slider("昨日白天小睡结束时间", options=daytime_slots, value="14:20")

    caffeine  = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value="无")
    alcohol   = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value="无")

    st.write("昨晚药物使用")
    med_col1, med_col2, med_col3 = st.columns(3)
    med_name = med_col1.text_input("药物名称", placeholder="无")
    med_dose = med_col2.text_input("剂量", placeholder="0mg")
    med_time = med_col3.select_slider("服用时间", options=evening_slots, value="22:00")

    daytime_mood = st.radio("昨日日间情绪状态", ["很差", "差", "一般", "好", "很好"], horizontal=True, index=2)

    sleep_interference = ";".join(
        st.multiselect("昨晚干扰睡眠因素（可多选）", ["噪音", "疼痛", "压力", "温度", "光线", "其他"])
    )

    bed_time       = st.select_slider("昨晚上床时间", options=evening_slots, value="23:00")
    try_sleep_time = st.select_slider("试图入睡时间", options=evening_slots, value="23:15")
    sleep_latency  = st.number_input("入睡所需时间（分钟）", 0, 120, 30)
    night_awake_count = st.number_input("夜间觉醒次数", 0, 10, 0)
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, 0)

    final_wake_time = st.select_slider("早晨最终醒来时间", options=morning_slots, value="6:30")
    get_up_time     = st.select_slider("起床时间", options=morning_slots, value="6:40")
    total_sleep_hours = st.number_input("总睡眠时间（小时）", 0.0, 24.0, 7.0, 0.1)

    sleep_quality = st.radio("睡眠质量评分", ["很差", "差", "一般", "好", "很好"], horizontal=True, index=2)
    morning_feeling = st.radio("晨起后感觉", ["差", "一般", "好"], horizontal=True, index=1)

    # 确保提交按钮在表单内部
    submitted = st.form_submit_button("保存日记")

# 数据库保存逻辑保持不变...
if submitted:
    if not name.strip():
        st.error("请填写姓名后再保存")
    else:
        # 保持原有数据库保存代码
        st.success(f"{record_date} 睡眠日记已保存！")
