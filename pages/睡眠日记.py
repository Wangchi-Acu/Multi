import streamlit as st
import pymysql
import os
from datetime import datetime, timedelta
import pytz
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dashscope
from dashscope import Generation
import threading  # 新增
import queue      # 新增

# 自定义CSS样式（保持不变）
st.markdown("""
<style>
/* 原有样式保持不变 */
</style>
""", unsafe_allow_html=True)

# 初始化 session_state 变量
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        "name": "",
        "nap_duration": 0,
        "daytime_bed_minutes": 0,
        "caffeine": "无",
        "alcohol": "无",
        "med_name1": "无",
        "med_dose1": "0mg",
        "med_name2": "无",
        "med_dose2": "0mg",
        "med_time": "22:00",
        "daytime_mood": "中",
        "selected_interference": ["无"],
        "bed_time": "23:00",
        "try_sleep_time": "23:05",
        "sleep_latency": 30,
        "night_awake_count": 0,
        "night_awake_total": 0,
        "final_wake_time": "06:30",
        "get_up_time": "06:35",
        "sleep_quality": "中",
        "morning_feeling": "中"
    }

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
        if pd.isna(t) or t == "无":
            return None
        h, m = map(int, t.split(":"))
        return (h if h >= 12 else h + 24) * 60 + m
    except (ValueError, AttributeError):
        return None

# 分钟 → 时间字符串
def min_to_time(m):
    h, mi = divmod(int(m), 60)
    h = h - 24 if h >= 24 else h
    return f"{h:02d}:{mi:02d}"

# 生成时间选项
def generate_time_slots(start_hour, end_hour):
    slots = []
    for h in range(start_hour, end_hour + 1):
        hour = h % 24
        for m in range(0, 60, 5):
            slots.append(f"{hour:02d}:{m:02d}")
    return slots

# 绘图函数 - 所有次汇总图表
def plot_all_days(patient_name):
    df = run_query(
        """
        SELECT t1.* 
        FROM sleep_diary t1
        INNER JOIN (
            SELECT record_date, MAX(created_at) AS max_created_at
            FROM sleep_diary
            WHERE name = %s
            GROUP BY record_date
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

    night_cols = ["bed_time", "try_sleep_time", "final_wake_time", "get_up_time"]
    night_labels = ["上床时间", "闭眼准备入睡时间", "最终醒来时间", "起床时间"]
    data1 = []
    for col, label in zip(night_cols, night_labels):
        mins = df[col].apply(time_to_min)
        data1.append(go.Scatter(x=df["date_fmt"], y=mins, name=label,
                                mode="lines+markers+text", text=df[col],
                                textposition="top center"))
    fig1 = go.Figure(data1)
    fig1.update_layout(
        title="夜间关键时间点",
        yaxis=dict(showticklabels=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5)
    )
    st.plotly_chart(fig1, use_container_width=True)

    nap_cols = ["nap_start", "nap_end"]
    nap_labels = ["小睡开始时间", "小睡结束时间"]
    data2 = []
    for col, label in zip(nap_cols, nap_labels):
        mins = df[col].apply(lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]) if pd.notna(t) and t != "无" and t != "" else None)
        data2.append(go.Scatter(x=df["date_fmt"], y=mins, name=label,
                                mode="lines+markers+text", text=df[col],
                                textposition="top center"))
    fig2 = go.Figure(data2)
    fig2.update_layout(
        title="日间小睡时间",
        yaxis=dict(showticklabels=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1.02, xanchor="left")
    )
    st.plotly_chart(fig2, use_container_width=True)

    metrics = [("sleep_latency", "入睡所需时长（分钟）"),
               ("night_awake_count", "夜间觉醒次数"),
               ("night_awake_total", "夜间觉醒总时长（分钟）"),
               ("total_sleep_hours", "总睡眠时长（小时）"),
               ("sleep_efficiency", "睡眠效率（%）")]
    for col, title in metrics:
        fig = px.line(df, x="date_fmt", y=col, markers=True, title=title)
        fig.update_layout(xaxis_title="填写日期", yaxis_title=title)
        st.plotly_chart(fig, use_container_width=True)

    # 显示数据框（使用中文列名）
    df_display = df.copy()
    chinese_column_names = {
        "name": "姓名",
        "record_date": "记录日期",
        "entry_date": "填写日期",
        "nap_start": "日间小睡开始时间",
        "nap_end": "日间小睡结束时间",
        "daytime_bed_minutes": "日间卧床时间（分钟）",
        "nap_duration": "昨日白天小睡总时长（分钟）",
        "caffeine": "咖啡因摄入",
        "alcohol": "酒精摄入",
        "med_name": "药物名称",
        "med_dose": "药物剂量",
        "med_time": "服药时间",
        "daytime_mood": "日间情绪状态",
        "sleep_interference": "睡眠干扰因素",
        "bed_time": "上床时间",
        "try_sleep_time": "闭眼准备入睡时间",
        "sleep_latency": "入睡所需时间（分钟）",
        "night_awake_count": "夜间觉醒次数",
        "night_awake_total": "夜间觉醒总时长（分钟）",
        "final_wake_time": "早晨最终醒来时间",
        "get_up_time": "起床时间",
        "total_sleep_hours": "总睡眠时长（小时）",
        "sleep_efficiency": "睡眠效率（%）",
        "sleep_quality": "睡眠质量自我评价",
        "morning_feeling": "晨起后精神状态",
        "created_at": "创建时间",
        "date_fmt": "日期"
    }
    df_display.rename(columns=chinese_column_names, inplace=True)
    important_cols = [
        "姓名", "记录日期", "填写日期", "上床时间", "闭眼准备入睡时间", "入睡所需时间（分钟）",
        "夜间觉醒次数", "夜间觉醒总时长（分钟）", "早晨最终醒来时间", "起床时间",
        "总睡眠时长（小时）", "睡眠效率（%）", "睡眠质量自我评价", "晨起后精神状态",
        "日间小睡开始时间", "日间小睡结束时间", "日间卧床时间（分钟）", "昨日白天小睡总时长（分钟）",
        "日间情绪状态", "睡眠干扰因素", "咖啡因摄入", "酒精摄入", "药物名称", "药物剂量", "服药时间", "创建时间", "日期"
    ]
    existing_cols = [col for col in important_cols if col in df_display.columns]
    other_cols = [col for col in df_display.columns if col not in existing_cols]
    final_cols = existing_cols + other_cols
    df_display = df_display[final_cols]
    st.dataframe(df_display.reset_index(drop=True))

# 修改后的 AI 分析函数（启用 thinking）
def analyze_sleep_data_with_ai(patient_name):
    try:
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope.api_key:
            return "API密钥未配置，无法提供AI分析建议。"
        
        all_data = run_query(
            """
            SELECT t1.* 
            FROM sleep_diary t1
            INNER JOIN (
                SELECT record_date, MAX(created_at) AS max_created_at
                FROM sleep_diary
                WHERE name = %s
                GROUP BY record_date
            ) t2 
            ON t1.record_date = t2.record_date AND t1.created_at = t2.max_created_at
            ORDER BY t1.record_date ASC
            """,
            params=(patient_name,)
        )
        if all_data.empty:
            return "暂无数据可供分析。"
        
        privacy_safe_data = all_data.copy()
        columns_to_drop = ['name', 'entry_date', 'created_at']
        columns_to_keep = [col for col in privacy_safe_data.columns if col not in columns_to_drop]
        privacy_safe_data = privacy_safe_data[columns_to_keep]
        privacy_safe_data['record_date'] = pd.to_datetime(privacy_safe_data['record_date']).dt.strftime('%Y-%m-%d')
        
        data_summary = f"患者所有睡眠记录数据（已保护隐私）：\n"
        data_summary += f"记录总数：{len(privacy_safe_data)}条\n\n"
        data_summary += "详细记录：\n"
        for index, row in privacy_safe_data.iterrows():
            data_summary += f"日期: {row['record_date']}\n"
            for col in privacy_safe_data.columns:
                if col != 'record_date':
                    data_summary += f"  {col}: {row[col]}\n"
            data_summary += "\n"
        
        prompt = f"""
        你是一名专业的睡眠医学专家。请根据以下患者的所有睡眠记录数据，提供专业的分析和改善建议，但是回答的文本要体现严谨性，你只是AI分析，结果仅供参考：

        {data_summary}

        请从以下几个方面进行分析和建议：
        1. 睡眠质量总体评估（除了总体评估，还需要比较最近2天与之前的睡眠情况相比，有何变化。）
        2. 主要问题识别（如入睡困难、夜间频繁觉醒等）
        3. 可能的影响因素分析
        4. 具体的改善建议（包括生活习惯、睡前准备、环境优化等）

        请用中文回答，语言要专业但易懂，建议要具体可行。
        注意：数据中的日期信息已做隐私保护处理，仅保留记录日期用于分析时间趋势。
        """

        response = Generation.call(
            model='qwen-flash',
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7,
            enable_thinking=True,      # ✅ 启用推理过程
            result_format="message"    # ✅ 必须指定
        )
        
        if response.status_code == 200:
            # ✅ 修改：从 choices[0].message.content 获取内容
            content = response.output.choices[0].message.content
            thinking_content = response.output.choices[0].message.get('thinking', '') # 获取推理过程（如果存在）
            return {
                "content": content,
                "thinking": thinking_content
            }
        else:
            return f"AI分析失败：{response.message}"
            
    except Exception as e:
        return f"AI分析出错：{str(e)}"

# 新增：线程安全的 AI 分析封装
def analyze_sleep_data_with_ai_async(patient_name, result_queue):
    try:
        result = analyze_sleep_data_with_ai(patient_name)
        result_queue.put(("success", result))
    except Exception as e:
        result_queue.put(("error", str(e)))

# 生成时间选项
hour_options = [f"{h:02d}" for h in range(24)]
minute_options = [f"{m:02d}" for m in range(0, 60, 5)]

# 日期处理
beijing_tz = pytz.timezone('Asia/Shanghai')
now_beijing = datetime.now(beijing_tz)
today = now_beijing.date()
yesterday = today - timedelta(days=1)

# 安眠药物选项
med_options = [
    "无",
    "艾司唑仑 Estazolam",
    "阿普唑仑 Alprazolam",
    "右佐匹克隆 Eszopiclone",
    "佐匹克隆 Zopiclone",
    "唑吡坦 Zolpidem",
    "劳拉西泮 Lorazepam",
    "地西泮 Diazepam",
    "氯硝西泮 Clonazepam",
    "曲唑酮 Trazodone",
    "米氮平 Mirtazapine",
    "氟西泮 Flurazepam",
    "夸西泮 Quazepam",
    "替马西泮 Temazepam",
    "三唑仑 Triazolam",
    "扎来普隆 Zaleplon",
    "喹硫平 Quetiapine",
    "苏沃雷生 Suvorexant",
    "莱博雷生 Lemborexant",
    "达利雷生 Daridorexant",
    "雷美替胺 Ramelteon",
    "他司美琼 Tasimelteon",
    "多塞平 Doxepin",
    "仲丁巴比妥 Butabarbital",
    "司可巴比妥 Secobarbital",
    "苯海拉明 Diphenhydramine",
    "多西拉敏 Doxylamine",
    "加巴喷丁 Gabapentin",
    "普瑞巴林 Pregabalin",
    "卡马西平 Carbamazepine",
    "加巴喷丁缓释 Gabapentin enacarbil",
    "普拉克索 Pramipexole",
    "罗匹尼罗 Ropinirole",
    "罗替戈汀 Rotigotine",
    "莫达非尼 Modafinil",
    "阿莫达非尼 Armodafinil",
    "皮托利生 Pitolisant"
]

# 创建表单
with st.form("sleep_diary"):
    name = st.text_input("姓名", placeholder="请输入您的姓名", value=st.session_state.form_data["name"])
    
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        st.markdown('<div class="readonly-date">', unsafe_allow_html=True)
        record_date = st.date_input("记录日期（一般为填写日期前一天，无特殊情况无需改动）", yesterday, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_date2:
        st.markdown('<div class="readonly-date">', unsafe_allow_html=True)
        entry_date = st.date_input("填写日期", today, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("日间活动记录")
    nap_duration = st.number_input(
        "昨日白天小睡总时长（分钟）",
        min_value=0,
        max_value=600,
        value=st.session_state.form_data["nap_duration"],
        step=5,
        help="白天小睡的总时长"
    )
    daytime_bed_minutes = st.number_input(
        "日间卧床时间（分钟）",
        min_value=0,
        max_value=600,
        value=st.session_state.form_data["daytime_bed_minutes"],
        step=5
    )
    caffeine = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value=st.session_state.form_data["caffeine"])
    alcohol = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value=st.session_state.form_data["alcohol"])
    
    st.subheader("安眠药物使用")
    med_name1 = st.selectbox("安眠药物①名称", options=med_options, index=med_options.index(st.session_state.form_data["med_name1"]) if st.session_state.form_data["med_name1"] in med_options else 0)
    med_dose1 = st.text_input("安眠药物①剂量", placeholder="0mg", value=st.session_state.form_data["med_dose1"])
    med_name2 = st.selectbox("安眠药物②名称", options=med_options, index=med_options.index(st.session_state.form_data["med_name2"]) if st.session_state.form_data["med_name2"] in med_options else 0)
    med_dose2 = st.text_input("安眠药物②剂量", placeholder="0mg", value=st.session_state.form_data["med_dose2"])
    
    col_med_time1, col_med_time2 = st.columns(2)
    with col_med_time1:
        med_time_parts = st.session_state.form_data["med_time"].split(":")
        med_time_hour = med_time_parts[0] if len(med_time_parts) == 2 else "22"
        med_hour = st.selectbox("安眠药物服用时间（时）", options=hour_options, index=hour_options.index(med_time_hour))
    with col_med_time2:
        med_time_parts = st.session_state.form_data["med_time"].split(":")
        med_time_minute = med_time_parts[1] if len(med_time_parts) == 2 else "00"
        if med_time_minute not in minute_options:
            med_time_minute = "00"
        med_minute = st.selectbox("安眠药物服用时间（分）", options=minute_options, index=minute_options.index(med_time_minute))
    med_time = f"{med_hour}:{med_minute}"
    
    daytime_mood = st.radio("昨日日间情绪状态", ["优", "良", "中", "差", "很差"], horizontal=True, index=["优", "良", "中", "差", "很差"].index(st.session_state.form_data["daytime_mood"]))
    
    interference_options = ["噪音", "疼痛", "压力", "温度", "光线", "其他", "无"]
    selected_interference = st.multiselect("昨晚干扰睡眠因素（可多选）", 
                                          interference_options, 
                                          default=st.session_state.form_data["selected_interference"])
    if "无" in selected_interference:
        sleep_interference = "无"
    elif not selected_interference:
        sleep_interference = "无"
    else:
        sleep_interference = ";".join(selected_interference)
    
    st.subheader("夜间睡眠记录")
    col_bed1, col_bed2 = st.columns(2)
    with col_bed1:
        bed_time_parts = st.session_state.form_data["bed_time"].split(":")
        bed_time_hour = bed_time_parts[0] if len(bed_time_parts) == 2 else "23"
        bed_hour = st.selectbox("昨晚上床时间（时）", options=hour_options, index=hour_options.index(bed_time_hour))
    with col_bed2:
        bed_time_parts = st.session_state.form_data["bed_time"].split(":")
        bed_time_minute = bed_time_parts[1] if len(bed_time_parts) == 2 else "00"
        if bed_time_minute not in minute_options:
            bed_time_minute = "00"
        bed_minute = st.selectbox("昨晚上床时间（分）", options=minute_options, index=minute_options.index(bed_time_minute))
    bed_time = f"{bed_hour}:{bed_minute}"
    
    col_try1, col_try2 = st.columns(2)
    with col_try1:
        try_time_parts = st.session_state.form_data["try_sleep_time"].split(":")
        try_time_hour = try_time_parts[0] if len(try_time_parts) == 2 else "23"
        try_hour = st.selectbox("闭眼准备入睡时间（时）", options=hour_options, index=hour_options.index(try_time_hour))
    with col_try2:
        try_time_parts = st.session_state.form_data["try_sleep_time"].split(":")
        try_time_minute = try_time_parts[1] if len(try_time_parts) == 2 else "05"
        if try_time_minute not in minute_options:
            try_time_minute = "05"
        try_minute = st.selectbox("闭眼准备入睡时间（分）", options=minute_options, index=minute_options.index(try_time_minute))
    try_sleep_time = f"{try_hour}:{try_minute}"
    
    col3, col4 = st.columns(2)
    sleep_latency = col3.number_input("入睡所需时间（分钟）", 0, 800, value=st.session_state.form_data["sleep_latency"])
    night_awake_count = col4.number_input("夜间觉醒次数", 0, 15, value=st.session_state.form_data["night_awake_count"])
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, value=st.session_state.form_data["night_awake_total"])

    col_final1, col_final2 = st.columns(2)
    with col_final1:
        final_time_parts = st.session_state.form_data["final_wake_time"].split(":")
        final_time_hour = final_time_parts[0] if len(final_time_parts) == 2 else "06"
        final_hour = st.selectbox("早晨最终醒来时间（时）", options=hour_options, index=hour_options.index(final_time_hour))
    with col_final2:
        final_time_parts = st.session_state.form_data["final_wake_time"].split(":")
        final_time_minute = final_time_parts[1] if len(final_time_parts) == 2 else "30"
        if final_time_minute not in minute_options:
            final_time_minute = "30"
        final_minute = st.selectbox("早晨最终醒来时间（分）", options=minute_options, index=minute_options.index(final_time_minute))
    final_wake_time = f"{final_hour}:{final_minute}"
    
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        up_time_parts = st.session_state.form_data["get_up_time"].split(":")
        up_time_hour = up_time_parts[0] if len(up_time_parts) == 2 else "06"
        up_hour = st.selectbox("起床时间（时）", options=hour_options, index=hour_options.index(up_time_hour))
    with col_up2:
        up_time_parts = st.session_state.form_data["get_up_time"].split(":")
        up_time_minute = up_time_parts[1] if len(up_time_parts) == 2 else "35"
        if up_time_minute not in minute_options:
            up_time_minute = "35"
        up_minute = st.selectbox("起床时间（分）", options=minute_options, index=minute_options.index(up_time_minute))
    get_up_time = f"{up_hour}:{up_minute}"

    try_sleep_min = time_to_min(try_sleep_time)
    final_wake_min = time_to_min(final_wake_time)
    if final_wake_min is not None and try_sleep_min is not None:
        if final_wake_min >= try_sleep_min:
            sleep_duration_min = final_wake_min - try_sleep_min
        else:
            sleep_duration_min = (24 * 60) - try_sleep_min + final_wake_min
        total_sleep_minutes = max(0, sleep_duration_min - night_awake_total - sleep_latency)
        total_sleep_hours = total_sleep_minutes / 60.0
    else:
        total_sleep_minutes = 0
        total_sleep_hours = 0.0

    bed_min = time_to_min(bed_time)
    get_up_min = time_to_min(get_up_time)
    if bed_min is not None and get_up_min is not None:
        if get_up_min >= bed_min:
            time_in_bed_min = get_up_min - bed_min
        else:
            time_in_bed_min = (24 * 60) - bed_min + get_up_min
        if time_in_bed_min > 0:
            sleep_efficiency = (total_sleep_minutes / time_in_bed_min) * 100
        else:
            sleep_efficiency = 0.0
    else:
        sleep_efficiency = 0.0

    st.markdown('<div class="readonly-data">', unsafe_allow_html=True)
    col_sleep1, col_sleep2 = st.columns(2)
    with col_sleep1:
        st.markdown(f"**总睡眠时间:** {total_sleep_hours:.2f} 小时 ({total_sleep_minutes} 分钟)")
    with col_sleep2:
        st.markdown(f"**睡眠效率:** {sleep_efficiency:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    sleep_quality = st.radio("睡眠质量自我评价", ["优", "良", "中", "差", "很差"], horizontal=True, index=["优", "良", "中", "差", "很差"].index(st.session_state.form_data["sleep_quality"]))
    morning_feeling_options = ["好", "中", "差"]
    morning_feeling = st.radio("晨起后精神状态", morning_feeling_options, horizontal=True, 
                              index=["好", "中", "差"].index(st.session_state.form_data["morning_feeling"]))
    
    submitted = st.form_submit_button("保存日记")

# 表单未提交时更新 session_state
if not submitted:
    st.session_state.form_data.update({
        "name": name,
        "nap_duration": nap_duration,
        "daytime_bed_minutes": daytime_bed_minutes,
        "caffeine": caffeine,
        "alcohol": alcohol,
        "med_name1": med_name1,
        "med_dose1": med_dose1,
        "med_name2": med_name2,
        "med_dose2": med_dose2,
        "med_time": med_time,
        "daytime_mood": daytime_mood,
        "selected_interference": selected_interference,
        "bed_time": bed_time,
        "try_sleep_time": try_sleep_time,
        "sleep_latency": sleep_latency,
        "night_awake_count": night_awake_count,
        "night_awake_total": night_awake_total,
        "final_wake_time": final_wake_time,
        "get_up_time": get_up_time,
        "sleep_quality": sleep_quality,
        "morning_feeling": morning_feeling
    })

# 提交逻辑
if submitted:
    bed_min = time_to_min(bed_time)
    try_sleep_min = time_to_min(try_sleep_time)
    final_wake_min = time_to_min(final_wake_time)
    get_up_min = time_to_min(get_up_time)
    
    errors = []
    if bed_min is None or try_sleep_min is None:
        errors.append("时间格式错误，请检查时间输入。")
    elif bed_min > try_sleep_min:
        errors.append("上床时间不能晚于闭眼准备入睡时间，请重新选择。")
    if final_wake_min is not None and get_up_min is not None:
        if get_up_min < final_wake_min:
            errors.append("起床时间不能早于早晨最终醒来时间，请重新选择。")
    elif final_wake_min is not None or get_up_min is not None:
        errors.append("时间格式错误，请检查早晨最终醒来时间和起床时间的输入。")
    if not name.strip():
        errors.append("请填写姓名后再保存。")
    
    if errors:
        error_html = """
        <div style="
            background-color: #f8d7da;
            border: 2px solid #f5c6cb;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        ">
            <h3 style="color: #721c24; margin: 0;">⚠️ 发现错误</h3>
            <p style="font-size: 18px; color: #721c24; margin: 10px 0 0 0;">
        """
        for error in errors:
            error_html += f"<strong>{error}</strong><br>"
        error_html += "</p></div>"
        st.markdown(error_html, unsafe_allow_html=True)
    else:
        try:
            record = {
                "name": name,
                "record_date": record_date.isoformat(),
                "entry_date": entry_date.isoformat(),
                "nap_start": "无",
                "nap_end": "无",
                "daytime_bed_minutes": daytime_bed_minutes,
                "nap_duration": nap_duration,
                "caffeine": caffeine,
                "alcohol": alcohol,
                "med_name": f"{med_name1};{med_name2}",
                "med_dose": f"{med_dose1};{med_dose2}",
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
                "sleep_efficiency": sleep_efficiency,
                "sleep_quality": sleep_quality,
                "morning_feeling": morning_feeling
            }

            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
                <div style="
                    background-color: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                ">
                    <h2 style="color: #856404; margin: 0;">⏳ 日记正在保存</h2>
                    <p style="font-size: 18px; color: #856404; margin: 10px 0 0 0;">
                        <strong>请勿离开页面，正在处理中...</strong>
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            conn = pymysql.connect(
                host=os.getenv("SQLPUB_HOST"),
                port=int(os.getenv("SQLPUB_PORT", 3307)),
                user=os.getenv("SQLPUB_USER"),
                password=os.getenv("SQLPUB_PWD"),
                database=os.getenv("SQLPUB_DB"),
                charset="utf8mb4"
            )
            
            with conn.cursor() as cursor:
                check_sql = """
                SELECT COUNT(*) FROM sleep_diary 
                WHERE name = %(name)s AND record_date = %(record_date)s
                """
                cursor.execute(check_sql, {"name": name, "record_date": record_date.isoformat()})
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    update_sql = """
                    UPDATE sleep_diary
                    SET entry_date = %(entry_date)s,
                        nap_start = %(nap_start)s,
                        nap_end = %(nap_end)s,
                        daytime_bed_minutes = %(daytime_bed_minutes)s,
                        nap_duration = %(nap_duration)s,
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
                        sleep_efficiency = %(sleep_efficiency)s,
                        sleep_quality = %(sleep_quality)s,
                        morning_feeling = %(morning_feeling)s
                    WHERE name = %(name)s AND record_date = %(record_date)s
                    """
                    cursor.execute(update_sql, record)
                    action = "更新"
                else:
                    insert_sql = """
                    INSERT INTO sleep_diary
                    (name, record_date, entry_date, nap_start, nap_end, daytime_bed_minutes, nap_duration, caffeine, alcohol, 
                     med_name, med_dose, med_time, daytime_mood, sleep_interference, 
                     bed_time, try_sleep_time, sleep_latency, night_awake_count, 
                     night_awake_total, final_wake_time, get_up_time, total_sleep_hours,
                     sleep_efficiency, sleep_quality, morning_feeling)
                    VALUES
                    (%(name)s, %(record_date)s, %(entry_date)s, %(nap_start)s, %(nap_end)s, 
                     %(daytime_bed_minutes)s, %(nap_duration)s, %(caffeine)s, %(alcohol)s, %(med_name)s, %(med_dose)s, %(med_time)s, 
                     %(daytime_mood)s, %(sleep_interference)s, %(bed_time)s, %(try_sleep_time)s, 
                     %(sleep_latency)s, %(night_awake_count)s, %(night_awake_total)s, 
                     %(final_wake_time)s, %(get_up_time)s, %(total_sleep_hours)s, 
                     %(sleep_efficiency)s, %(sleep_quality)s, %(morning_feeling)s)
                    """
                    cursor.execute(insert_sql, record)
                    action = "保存"
            
            conn.commit()
            conn.close()
            loading_placeholder.empty()
            st.success("✅ 日记保存完成！向下滑动可查看近期睡眠情况及AI分析！")
            
            st.session_state.form_data = {
                "name": "",
                "nap_duration": 0,
                "daytime_bed_minutes": 0,
                "caffeine": "无",
                "alcohol": "无",
                "med_name1": "无",
                "med_dose1": "0mg",
                "med_name2": "无",
                "med_dose2": "0mg",
                "med_time": "22:00",
                "daytime_mood": "中",
                "selected_interference": ["无"],
                "bed_time": "23:00",
                "try_sleep_time": "23:05",
                "sleep_latency": 30,
                "night_awake_count": 0,
                "night_awake_total": 0,
                "final_wake_time": "06:30",
                "get_up_time": "06:35",
                "sleep_quality": "中",
                "morning_feeling": "中"
            }
            
            st.subheader("📊 您所有次的睡眠情况")
            plot_all_days(name)
            
            # ✅ 新增：带推理过程展示的 AI 分析（关键部分）
            st.subheader("🤖 AI睡眠分析与建议")

            result_queue = queue.Queue()
            thread = threading.Thread(target=analyze_sleep_data_with_ai_async, args=(name, result_queue))
            thread.start()

            # 等待线程完成（最多等待20秒）
            thread.join(timeout=20)

            if not result_queue.empty():
                status_type, message = result_queue.get()
                if status_type == "success":
                    if isinstance(message, dict): # 检查是否为新的返回格式
                        content = message.get("content", "")
                        thinking_content = message.get("thinking", "")
                        
                        # 如果有推理过程，先展示
                        if thinking_content:
                            with st.expander("🔬 AI 推理过程（点击展开）", expanded=False):
                                st.markdown(f"<div style='white-space: pre-wrap;'>{thinking_content}</div>", unsafe_allow_html=True)
                        
                        # 展示最终分析结果
                        st.markdown(f"""
                            <div style="
                                background-color: #f8f9fa;
                                border-left: 4px solid #007bff;
                                padding: 20px;
                                border-radius: 5px;
                                margin: 20px 0;
                            ">
                                <h4>📋 个性化睡眠分析报告</h4>
                                <div style="line-height: 1.6;">{content}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        # 兼容旧的字符串返回格式
                        st.markdown(f"""
                            <div style="
                                background-color: #f8f9fa;
                                border-left: 4px solid #007bff;
                                padding: 20px;
                                border-radius: 5px;
                                margin: 20px 0;
                            ">
                                <h4>📋 个性化睡眠分析报告</h4>
                                <div style="line-height: 1.6;">{message}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"AI分析失败：{message}")
            else:
                st.warning("AI 分析响应较慢，仍在后台处理中，请勿离开此页面。")

        except Exception as e:
            st.error(f"操作失败: {str(e)}")
