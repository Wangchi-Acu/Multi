import streamlit as st
import pymysql, os
from datetime import date, datetime

st.set_page_config(page_title="睡眠日记", layout="centered")
st.title("🛏️ 国际标准睡眠日记（核心版）")

# 生成中文日期
def chinese_date(dt):
    wd = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][dt.weekday()]
    return dt.strftime("%Y年%m月%d日") + " " + wd

# 时间滑块刻度（20:00-02:00）
evening_slots = [f"{h:02d}:{m:02d}" for h in range(20, 24) for m in range(60)] + \
                [f"00:{m:02d}" for m in range(60)] + \
                [f"01:{m:02d}" for m in range(60)] + ["02:00"]

# 早晨时间滑块（02:00-12:00）
morning_slots = [f"{h:02d}:{m:02d}" for h in range(2, 13) for m in range(60)]

with st.form("sleep_diary"):
    name = st.text_input("姓名")
    record_date = st.date_input("记录日期", date.today(), format="YYYY年MM月DD日")
    st.write("记录日期：" + chinese_date(record_date))

    col1, col2 = st.columns(2)
    nap_start = col1.select_slider("昨日白天小睡开始时间", options=evening_slots, value="14:00")
    nap_end   = col2.select_slider("昨日白天小睡结束时间", options=evening_slots, value="14:20")

    caffeine = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value="无")
    alcohol  = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value="无")

    st.write("昨晚药物使用")
    med_col1, med_col2, med_col3 = st.columns(3)
    med_name = med_col1.text_input("药物名称", placeholder="无")
    med_dose = med_col2.text_input("剂量", placeholder="0mg")
    med_time = med_col3.select_slider("服用时间", options=evening_slots, value="22:00")

    daytime_mood = st.radio("昨日日间情绪状态", ["很差", "差", "一般", "好", "很好"], horizontal=True)
    sleep_interference = ";".join(st.multiselect(
        "昨晚干扰睡眠因素（可多选）",
        ["噪音", "疼痛", "压力", "温度", "光线", "其他"]
    ))

    bed_time       = st.select_slider("昨晚上床时间", options=evening_slots, value="23:00")
    try_sleep_time = st.select_slider("试图入睡时间", options=evening_slots, value="23:15")
    sleep_latency  = st.number_input("入睡所需时间（分钟）", 0, 120, 30)
    night_awake_count = st.number_input("夜间觉醒次数", 0, 10, 0)
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, 0)

    final_wake_time = st.select_slider("早晨最终醒来时间", options=morning_slots, value="6:30")
    get_up_time     = st.select_slider("起床时间", options=morning_slots, value="6:40")
    total_sleep_hours = st.number_input("总睡眠时间（小时）", 0.0, 24.0, 7.0, 0.1)

    sleep_quality = st.radio("睡眠质量评分", ["很差", "差", "一般", "好", "很好"], horizontal=True)
    morning_feeling = st.radio("晨起后感觉", ["差", "一般", "好"], horizontal=True)

    submitted = st.form_submit_button("保存日记")

# 保存
if submitted:
    if not name.strip():
        st.error("请填写姓名后再保存")
    else:
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
        conn.cursor().execute(sql, record)
        conn.commit()
        conn.close()
        st.success(f"{record_date} 睡眠日记已保存！")
