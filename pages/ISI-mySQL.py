import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import pymysql  # 使用 PyMySQL 替代 psycopg2

def save_csv_isi(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['时间戳']}_{name}_ISI.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def save_sqlpub(record: dict):
    """把同一条记录写入 MySQL 数据库"""
    try:
        # 从 Streamlit Secrets 获取数据库连接信息
        conn = pymysql.connect(
            host=st.secrets["SQLPUB_HOST"],
            port=st.secrets["SQLPUB_PORT"],
            database=st.secrets["SQLPUB_DB"],
            user=st.secrets["SQLPUB_USER"],
            password=st.secrets["SQLPUB_PWD"],
            charset='utf8mb4'
        )
        
        sql = """
        INSERT INTO isi_record
        (name, ts,
         q1a_opt, q1a_score,
         q1b_opt, q1b_score,
         q1c_opt, q1c_score,
         q2_opt,  q2_score,
         q3_opt,  q3_score,
         q4_opt,  q4_score,
         q5_opt,  q5_score,
         total_score)
        VALUES
        (%s, %s,
         %s, %s,
         %s, %s,
         %s, %s,
         %s, %s,
         %s, %s,
         %s, %s,
         %s, %s,
         %s)
        """
        
        with conn.cursor() as cur:
            cur.execute(sql, (
                record["姓名"],
                record["时间戳"],
                record["1a. 入睡困难(选项)"],
                record["1a. 入睡困难(分值)"],
                record["1b. 睡眠维持困难(选项)"],
                record["1b. 睡眠维持困难(分值)"],
                record["1c. 早醒(选项)"],
                record["1c. 早醒(分值)"],
                record["2. 睡眠满意度(选项)"],
                record["2. 睡眠满意度(分值)"],
                record["3. 日常功能影响(选项)"],
                record["3. 日常功能影响(分值)"],
                record["4. 生活质量影响(选项)"],
                record["4. 生活质量影响(分值)"],
                record["5. 担心程度(选项)"],
                record["5. 担心程度(分值)"],
                record["总分"]
            ))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"数据库写入失败：{str(e)}")
        return False
    finally:
        if conn:
            conn.close()

# ---------- Streamlit 界面 ----------
st.set_page_config(page_title="失眠严重指数量表 （ISI）", layout="centered")
st.image("jsszyylogo.png", width=500)
st.title("江苏省中医院针灸科失眠专病门诊")
st.markdown(
    "<h3 style='color:#555555;'>失眠严重指数量表（ISI）在线问卷</h3>",
    unsafe_allow_html=True
)

# 1. 先放姓名
name = st.text_input("姓名")

score_map = {
    "无": 0, "轻度": 1, "中度": 2, "重度": 3, "极重度": 4,
    "很满意": 0, "满意": 1, "一般": 2, "不满意": 3, "很不满意": 4,
    "没有干扰": 0, "轻微": 1, "有些": 2, "较多": 3, "很多": 4,
    "没有": 0, "轻微": 1, "有些": 2, "较多": 3, "很多": 4
}

questions = [
    ("1a. 入睡困难", ["无", "轻度", "中度", "重度", "极重度"]),
    ("1b. 睡眠维持困难", ["无", "轻度", "中度", "重度", "极重度"]),
    ("1c. 早醒", ["无", "轻度", "中度", "重度", "极重度"]),
    ("2. 睡眠满意度", ["很满意", "满意", "一般", "不满意", "很不满意"]),
    ("3. 日常功能影响", ["没有干扰", "轻微", "有些", "较多", "很多"]),
    ("4. 生活质量影响", ["没有", "轻微", "有些", "较多", "很多"]),
    ("5. 担心程度", ["没有", "轻微", "有些", "较多", "很多"])
]

# 2. 收集答案
choices = {}
for txt, opts in questions:
    choices[txt] = st.radio(txt, opts, horizontal=True, key=txt)

# 3. 提交按钮
if st.button("提交 ISI"):
    if not name:
        st.warning("请输入姓名")
        st.stop()

    # 生成记录
    record = {"姓名": name, "时间戳": datetime.now().strftime("%Y%m%d%H%M")}
    total = 0
    for txt, opts in questions:
        opt = choices[txt]
        val = score_map[opt]
        record[f"{txt}(选项)"] = opt
        record[f"{txt}(分值)"] = val
        total += val
    record["总分"] = total

    # 保存到CSV
    csv_path = save_csv_isi(name, record)
    
    # 保存到数据库
    db_success = save_sqlpub(record)
    
    # 展示结果
    st.subheader("评分结果")
    st.write(f"**总分：{total}**")
    
    # 显示分数解释
    if total <= 7:
        st.success("**临床意义：无显著失眠**")
    elif total <= 14:
        st.warning("**临床意义：轻度失眠**")
    elif total <= 21:
        st.error("**临床意义：中度失眠**")
    else:
        st.error("**临床意义：重度失眠**")
    
    # 显示详细结果
    for k, v in choices.items():
        st.write(f"- {k}：{v}（{score_map[v]} 分）")

    # 下载按钮
    with open(csv_path, "rb") as f:
        st.download_button(
            label="📥 下载结果 CSV",
            data=f,
            file_name=os.path.basename(csv_path),
            mime="text/csv"
        )
    
    if db_success:
        st.success("问卷提交成功！数据已保存到数据库")
    else:
        st.warning("问卷提交成功（本地CSV已保存），但数据库保存失败")
