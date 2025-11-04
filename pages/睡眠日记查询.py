import streamlit as st
import pymysql
import os
import pandas as pd

st.set_page_config(page_title="睡眠日记查询", layout="wide")
st.image("jsszyylogo.png", width=500)
st.markdown("""
<div style='color: #000000; padding: 2px; border-radius: 15px; text-align: left;'>
    <h1 style='font-size: 37px; margin: 0; font-weight: 700;'>江苏省中医院针灸科</h1>
    <h1 style='font-size: 32px; margin: -15px 0 0 0; font-weight: 600;'>失眠专病门诊</h1>
</div>
""", unsafe_allow_html=True)
st.title("🔍 睡眠日记查询")

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

# 单次查询功能
st.subheader("📋 单次查询")

with st.form("query_form"):
    query_name = st.text_input("请输入患者姓名")
    query_submitted = st.form_submit_button("查询")

if query_submitted:
    if not query_name.strip():
        st.error("请输入患者姓名")
    else:
        try:
            # 查询患者的所有记录
            sql = """
            SELECT *
            FROM sleep_diary
            WHERE name = %s
            ORDER BY record_date DESC, created_at DESC
            """
            df = run_query(sql, params=(query_name,))
            
            if df.empty:
                st.warning("未找到该患者的记录")
            else:
                st.success(f"找到 {len(df)} 条记录")
                
                # 将列名替换为中文
                df_display = df.copy()
                df_display.columns = [field_mapping.get(col, col) for col in df_display.columns]
                
                # 重新排列列的顺序，将重要的信息放在前面
                important_cols = [
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
                
                # 显示所有记录
                st.dataframe(df_display, use_container_width=True)
                
                # 为每条记录创建详细查看
                for idx, row in df.iterrows():
                    with st.expander(f"记录详情 - 日期: {row['record_date']} (创建时间: {row['created_at']})"):
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
        
        except Exception as e:
            st.error(f"查询失败: {str(e)}")

# 其他原有功能保持不变
st.subheader("📅 按日期范围查询")
with st.form("date_range_form"):
    col1, col2 = st.columns(2)
    start_date = col1.date_input("开始日期")
    end_date = col2.date_input("结束日期")
    range_name = st.text_input("患者姓名（可选）")
    range_submitted = st.form_submit_button("按日期范围查询")

if range_submitted:
    try:
        sql = """
        SELECT *
        FROM sleep_diary
        WHERE record_date BETWEEN %s AND %s
        """
        params = [start_date, end_date]
        
        if range_name.strip():
            sql += " AND name = %s"
            params.append(range_name)
        
        sql += " ORDER BY record_date DESC, created_at DESC"
        
        df = run_query(sql, params=tuple(params))
        
        if df.empty:
            st.warning("未找到符合条件的记录")
        else:
            # 将列名替换为中文
            df_display = df.copy()
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
            
            st.success(f"找到 {len(df)} 条记录")
            st.dataframe(df_display, use_container_width=True)
    
    except Exception as e:
        st.error(f"查询失败: {str(e)}")

st.subheader("📊 查询统计")
with st.form("stats_form"):
    stats_name = st.text_input("请输入患者姓名（用于统计）")
    stats_submitted = st.form_submit_button("获取统计信息")

if stats_submitted:
    if not stats_name.strip():
        st.error("请输入患者姓名")
    else:
        try:
            # 获取统计信息
            sql = """
            SELECT 
                COUNT(*) as 总记录数,
                MIN(record_date) as 首次记录日期,
                MAX(record_date) as 最近记录日期,
                AVG(total_sleep_hours) as 平均睡眠时长,
                AVG(sleep_latency) as 平均入睡时间,
                AVG(night_awake_count) as 平均夜间觉醒次数,
                AVG(night_awake_total) as 平均夜间觉醒总时长
            FROM sleep_diary
            WHERE name = %s
            """
            stats_df = run_query(sql, params=(stats_name,))
            
            if stats_df.iloc[0]['总记录数'] == 0:
                st.warning("未找到该患者的记录")
            else:
                stats = stats_df.iloc[0]
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("总记录数", int(stats['总记录数']))
                    st.metric("平均睡眠时长", f"{stats['平均睡眠时长']:.2f} 小时")
                
                with col2:
                    st.metric("首次记录日期", str(stats['首次记录日期']))
                    st.metric("平均入睡时间", f"{stats['平均入睡时间']:.1f} 分钟")
                
                with col3:
                    st.metric("最近记录日期", str(stats['最近记录日期']))
                    st.metric("平均夜间觉醒次数", f"{stats['平均夜间觉醒次数']:.1f} 次")
                
                st.markdown(f"**平均夜间觉醒总时长:** {stats['平均夜间觉醒总时长']:.1f} 分钟")
        
        except Exception as e:
            st.error(f"统计查询失败: {str(e)}")
