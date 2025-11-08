import streamlit as st
import pymysql
import os
from datetime import datetime, timedelta # 修改：导入 datetime
import pytz # 新增：导入 pytz 库用于时区处理
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dashscope
from dashscope import Generation

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
        h, m = map(int, t.split(":"))
        return (h if h >= 12 else h + 24) * 60 + m
    except:
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
        yaxis=dict(
            tickformat="%H:%M", 
            autorange=True,
            showticklabels=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5)
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1.02, xanchor="left")
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 3-7 其余指标
    metrics = [("sleep_latency", "入睡所需时长（分钟）"),
               ("night_awake_count", "夜间觉醒次数"),
               ("night_awake_total", "夜间觉醒总时长（分钟）"),
               ("total_sleep_hours", "总睡眠时长（小时）"),
               ("sleep_efficiency", "睡眠效率（%）")]
    for col, title in metrics:
        fig = px.line(df, x="date_fmt", y=col, markers=True, title=title)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df.reset_index(drop=True))

# AI分析函数 - 修改为提供所有数据但保护隐私
def analyze_sleep_data_with_ai(patient_name):
    """
    使用通义千问API分析患者的所有睡眠数据并给出建议（保护隐私）
    """
    try:
        # 设置API密钥（建议从环境变量获取）
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not dashscope.api_key:
            return "API密钥未配置，无法提供AI分析建议。"
        
        # 获取患者的所有睡眠数据
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
        
        # 保护隐私：只保留必要的数据，移除姓名和敏感日期信息
        # 只保留record_date和其他睡眠相关数据
        privacy_safe_data = all_data.copy()
        
        # 移除隐私信息
        columns_to_drop = ['name', 'entry_date', 'created_at']  # 移除姓名和填写日期
        columns_to_keep = [col for col in privacy_safe_data.columns if col not in columns_to_drop]
        privacy_safe_data = privacy_safe_data[columns_to_keep]
        
        # 格式化record_date为更友好的显示格式
        privacy_safe_data['record_date'] = pd.to_datetime(privacy_safe_data['record_date']).dt.strftime('%Y-%m-%d')
        
        # 准备数据摘要
        data_summary = f"患者所有睡眠记录数据（已保护隐私）：\n"
        data_summary += f"记录总数：{len(privacy_safe_data)}条\n\n"
        
        # 添加所有记录的详细数据
        data_summary += "详细记录：\n"
        for index, row in privacy_safe_data.iterrows():
            data_summary += f"日期: {row['record_date']}\n"
            for col in privacy_safe_data.columns:
                if col != 'record_date':
                    data_summary += f"  {col}: {row[col]}\n"
            data_summary += "\n"
        
        # 构建提示词
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

        # 调用通义千问API
        response = Generation.call(
            model='qwen-plus',
            prompt=prompt,
            max_tokens=1500,
            temperature=0.7
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            return f"AI分析失败：{response.message}"
            
    except Exception as e:
        return f"AI分析出错：{str(e)}"

# 生成时间选项
daytime_slots = generate_time_slots(6, 20)  # 白天时间：06:00-20:00
evening_slots = generate_time_slots(20, 26)  # 晚上时间：20:00-02:00（26=02:00+24）
morning_slots = generate_time_slots(2, 12)   # 早晨时间：02:00-12:00

# 日期处理 - 修改：使用北京时间
beijing_tz = pytz.timezone('Asia/Shanghai') # 定义北京时间时区
now_beijing = datetime.now(beijing_tz)      # 获取当前北京时间
today = now_beijing.date()                  # 提取日期部分
yesterday = today - timedelta(days=1)       # 计算昨天日期

# 安眠药物选项
med_options = [
    "无",
    "艾司唑仑 Estazolam（ProSom）",
    "佐匹克隆 Eszopiclone（Lunesta）",
    "唑吡坦 Zolpidem（Ambien、Edluar、Intermezzo、Zolpimist）",
    "劳拉西泮 Lorazepam（Ativan）",
    "地西泮 Diazepam（Valium）",
    "氯硝西泮 Clonazepam（Klonopin）",
    "曲唑酮 Trazodone",
    "米氮平 Mirtazapine（Remeron）",
    "氟西泮 Flurazepam（Dalmane）",
    "夸西泮 Quazepam（Doral）",
    "替马西泮 Temazepam（Restoril）",
    "三唑仑 Triazolam（Halcion）",
    "扎来普隆 Zaleplon（Sonata）",
    "喹硫平 Quetiapine（Seroquel）",
    "苏沃雷生 Suvorexant（Belsomra）",
    "莱博雷生 Lemborexant（Dayvigo）",
    "达利雷生 Daridorexant（Quviviq）",
    "雷美替胺 Ramelteon（Rozerem）",
    "他司美琼 Tasimelteon（Hetlioz）",
    "多塞平 Doxepin 3-6 mg（Silenor）",
    "仲丁巴比妥 Butabarbital（Butisol）",
    "司可巴比妥 Secobarbital（Seconal）",
    "苯海拉明 Diphenhydramine（Benadryl、Nytol、Sominex 等）",
    "多西拉敏 Doxylamine（Unisom）",
    "加巴喷丁 Gabapentin（Neurontin）",
    "普瑞巴林 Pregabalin（Lyrica）",
    "卡马西平 Carbamazepine（Tegretol）",
    "加巴喷丁缓释 Gabapentin enacarbil（Horizant）",
    "普拉克索 Pramipexole（Mirapex）",
    "罗匹尼罗 Ropinirole（Requip）",
    "罗替戈汀 Rotigotine（Neupro）",
    "莫达非尼 Modafinil（Provigil）",
    "阿莫达非尼 Armodafinil（Nuvigil）",
    "皮托利生 Pitolisant（Wakix）"
]

# 创建表单
with st.form("sleep_diary"):
    # 姓名和日期部分
    name = st.text_input("姓名", placeholder="请输入您的姓名", value=st.session_state.form_data["name"])
    
    col_date1, col_date2 = st.columns(2)
    # 记录日期（日记内容对应的日期，默认为昨天）
    with col_date1:
        st.markdown('<div class="readonly-date">', unsafe_allow_html=True)
        record_date = st.date_input("记录日期（一般为填写日期前一天，无特殊情况无需改动）", yesterday, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 填写日期（提交日记的日期，默认为今天，不可更改）
    with col_date2:
        st.markdown('<div class="readonly-date">', unsafe_allow_html=True)
        entry_date = st.date_input("填写日期", today, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("日间活动记录")
    # 添加“昨日白天小睡总时长”
    nap_duration = st.number_input(
        "昨日白天小睡总时长（分钟）",
        min_value=0,
        max_value=600,
        value=st.session_state.form_data["nap_duration"], # 从 session_state 加载
        step=5,
        help="白天小睡的总时长"
    )
    
    # 添加日间卧床时间（单位：分钟）
    daytime_bed_minutes = st.number_input(
        "日间卧床时间（分钟）",
        min_value=0,
        max_value=600,
        value=st.session_state.form_data["daytime_bed_minutes"], # 从 session_state 加载
        step=5,
        help="除小睡外，日间在床上休息但未入睡的时间"
    )
    
    caffeine = st.text_input("昨日咖啡因摄入（例：咖啡，8:00/2杯）", value=st.session_state.form_data["caffeine"]) # 从 session_state 加载
    alcohol = st.text_input("昨日酒精摄入（例：啤酒，19:00/1瓶）", value=st.session_state.form_data["alcohol"]) # 从 session_state 加载
    
    st.subheader("安眠药物使用")
    # 安眠药物①
    med_name1 = st.selectbox("安眠药物①名称", options=med_options, index=med_options.index(st.session_state.form_data["med_name1"]) if st.session_state.form_data["med_name1"] in med_options else 0) # 从 session_state 加载
    med_dose1 = st.text_input("安眠药物①剂量", placeholder="0mg", value=st.session_state.form_data["med_dose1"]) # 从 session_state 加载
    
    # 安眠药物②
    med_name2 = st.selectbox("安眠药物②名称", options=med_options, index=med_options.index(st.session_state.form_data["med_name2"]) if st.session_state.form_data["med_name2"] in med_options else 0) # 从 session_state 加载
    med_dose2 = st.text_input("安眠药物②剂量", placeholder="0mg", value=st.session_state.form_data["med_dose2"]) # 从 session_state 加载
    
    # 安眠药物服用时间 - 一直可填写状态
    med_time = st.select_slider("安眠药物服用时间", options=evening_slots, value=st.session_state.form_data["med_time"]) # 从 session_state 加载
    
    # 日间情绪状态
    daytime_mood = st.radio("昨日日间情绪状态", ["优", "良", "中", "差", "很差"], horizontal=True, index=["优", "良", "中", "差", "很差"].index(st.session_state.form_data["daytime_mood"])) # 从 session_state 加载
    
    # 干扰睡眠因素 - 添加"无"选项并设为默认
    interference_options = ["噪音", "疼痛", "压力", "温度", "光线", "其他", "无"]
    selected_interference = st.multiselect("昨晚干扰睡眠因素（可多选）", 
                                          interference_options, 
                                          default=st.session_state.form_data["selected_interference"]) # 从 session_state 加载
    
    # 如果用户选择了"无"和其他选项，则只保留"无"
    if "无" in selected_interference:
        sleep_interference = "无"
    elif not selected_interference:
        sleep_interference = "无"
    else:
        sleep_interference = ";".join(selected_interference)
    
    st.subheader("夜间睡眠记录")
    bed_time = st.select_slider("昨晚上床时间", options=evening_slots, value=st.session_state.form_data["bed_time"]) # 从 session_state 加载
    try_sleep_time = st.select_slider("闭眼准备入睡时间", options=evening_slots, value=st.session_state.form_data["try_sleep_time"]) # 从 session_state 加载
    
    col3, col4 = st.columns(2)
    sleep_latency = col3.number_input("入睡所需时间（分钟）", 0, 800, value=st.session_state.form_data["sleep_latency"]) # 从 session_state 加载
    night_awake_count = col4.number_input("夜间觉醒次数", 0, 15, value=st.session_state.form_data["night_awake_count"]) # 从 session_state 加载
    
    night_awake_total = st.number_input("夜间觉醒总时长（分钟）", 0, 300, value=st.session_state.form_data["night_awake_total"]) # 从 session_state 加载

    col5, col6 = st.columns(2)
    final_wake_time = col5.select_slider("早晨最终醒来时间", options=morning_slots, value=st.session_state.form_data["final_wake_time"]) # 从 session_state 加载
    get_up_time = col6.select_slider("起床时间", options=morning_slots, value=st.session_state.form_data["get_up_time"]) # 从 session_state 加载
    
    # 自动计算总睡眠时间（分钟）
    # 总睡眠时间 = (最终醒来时间 - 闭眼准备入睡时间) - 夜间觉醒总时长 - 入睡所需时间
    try_sleep_min = time_to_min(try_sleep_time)
    final_wake_min = time_to_min(final_wake_time)
    
    # 计算闭眼准备入睡到最终醒来的总时长（考虑跨天）
    if final_wake_min >= try_sleep_min:
        sleep_duration_min = final_wake_min - try_sleep_min
    else:
        sleep_duration_min = (24 * 60) - try_sleep_min + final_wake_min
    
    total_sleep_minutes = max(0, sleep_duration_min - night_awake_total - sleep_latency)
    total_sleep_hours = total_sleep_minutes / 60.0
    
    # 自动计算睡眠效率（%）
    # 睡眠效率 = 总睡眠时间 / (起床时间 - 上床时间)
    bed_min = time_to_min(bed_time)
    get_up_min = time_to_min(get_up_time)
    
    if get_up_min >= bed_min:
        time_in_bed_min = get_up_min - bed_min
    else:
        time_in_bed_min = (24 * 60) - bed_min + get_up_min
    
    if time_in_bed_min > 0:
        sleep_efficiency = (total_sleep_minutes / time_in_bed_min) * 100
    else:
        sleep_efficiency = 0.0
    
    # 显示自动计算的总睡眠时间和睡眠效率
    st.markdown('<div class="readonly-data">', unsafe_allow_html=True)
    col_sleep1, col_sleep2 = st.columns(2)
    with col_sleep1:
        st.markdown(f"**总睡眠时间:** {total_sleep_hours:.2f} 小时 ({total_sleep_minutes} 分钟)")
    with col_sleep2:
        st.markdown(f"**睡眠效率:** {sleep_efficiency:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 睡眠质量自我评价
    sleep_quality = st.radio("睡眠质量自我评价", ["优", "良", "中", "差", "很差"], horizontal=True, index=["优", "良", "中", "差", "很差"].index(st.session_state.form_data["sleep_quality"])) # 从 session_state 加载
    
    # 晨起后精神状态 - 改为好、中、差
    morning_feeling_options = ["好", "中", "差"]
    morning_feeling = st.radio("晨起后精神状态", morning_feeling_options, horizontal=True, 
                              index=["好", "中", "差"].index(st.session_state.form_data["morning_feeling"])) # 从 session_state 加载
    
    # 提交按钮
    submitted = st.form_submit_button("保存日记")

# 数据库连接和保存逻辑
if submitted:
    # 检查自检错误
    bed_min = time_to_min(bed_time)
    try_sleep_min = time_to_min(try_sleep_time)
    
    errors = []
    if bed_min > try_sleep_min:
        errors.append("上床时间不能晚于闭眼准备入睡时间，请重新选择。")
    if not name.strip():
        errors.append("请填写姓名后再保存。")
    
    if errors:
        # 显示醒目错误信息
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
            # 构建记录数据
            record = {
                "name": name,
                "record_date": record_date.isoformat(),  # 睡眠日期
                "entry_date": entry_date.isoformat(),    # 填写日期
                "nap_start": "无",  # 固定值
                "nap_end": "无",    # 固定值
                "daytime_bed_minutes": daytime_bed_minutes,  # 新增的日间卧床时间
                "nap_duration": nap_duration,  # 新增的白天小睡总时长
                "caffeine": caffeine,
                "alcohol": alcohol,
                "med_name": f"{med_name1};{med_name2}",  # 合并两个药物名称
                "med_dose": f"{med_dose1};{med_dose2}",  # 合并两个药物剂量
                "med_time": med_time,
                "daytime_mood": daytime_mood,
                "sleep_interference": sleep_interference,
                "bed_time": bed_time,
                "try_sleep_time": try_sleep_time,  # 闭眼准备入睡时间
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

            # 显示更醒目的加载提示
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
                    # 插入新记录
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
            
            # 清除加载提示并显示成功消息
            loading_placeholder.empty()
            st.success("✅ 日记保存完成！向下滑动可查看近期睡眠情况及AI分析！")
            
            # 保存成功后，清空 session_state 中的表单数据
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
            
            # 展示最近7次汇总图表
            st.subheader("📊 您最近7天的睡眠情况")
            plot_recent_7_days(name)
            
            # AI分析和建议
            st.subheader("🤖 AI睡眠分析与建议")
            
            # 获取所有数据用于AI分析（已保护隐私）
            ai_analysis_placeholder = st.empty()
            ai_analysis_placeholder.info("正在为您生成个性化的睡眠分析和建议...")
            
            try:
                ai_analysis_result = analyze_sleep_data_with_ai(name)
                ai_analysis_placeholder.empty()  # 清除加载提示
                st.markdown(f"""
                    <div style="
                        background-color: #f8f9fa;
                        border-left: 4px solid #007bff;
                        padding: 20px;
                        border-radius: 5px;
                        margin: 20px 0;
                    ">
                        <h4>📋 个性化睡眠分析报告</h4>
                        <div style="line-height: 1.6;">{ai_analysis_result}</div>
                    </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                ai_analysis_placeholder.error(f"AI分析失败：{str(e)}")
                
        except Exception as e:
            st.error(f"操作失败: {str(e)}")
else: # 如果没有提交表单，保存当前表单内容到 session_state
    # 更新 session_state 中的表单数据
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
