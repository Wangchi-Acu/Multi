import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

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
    
# ---------- Streamlit 界面 ----------
st.set_page_config(page_title="失眠严重指数量表 （ISI）", layout="centered")
st.image("jsszyylogo.png", width=500)  # 更改url_to_your_logo.png为你的logo图片链接，调整width为适当的大小
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
    ("1a. 入睡困难", ["无","轻度","中度","重度","极重度"]),
    ("1b. 睡眠维持困难", ["无","轻度","中度","重度","极重度"]),
    ("1c. 早醒", ["无","轻度","中度","重度","极重度"]),
    ("2. 睡眠满意度", ["很满意","满意","一般","不满意","很不满意"]),
    ("3. 日常功能影响", ["没有干扰","轻微","有些","较多","很多"]),
    ("4. 生活质量影响", ["没有","轻微","有些","较多","很多"]),
    ("5. 担心程度", ["没有","轻微","有些","较多","很多"])
]

# 2. 收集答案
choices = {}
for txt, opts in questions:
    choices[txt] = st.radio(txt, opts, horizontal=True)

# 3. 提交按钮（不在 form 内）
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

    # 保存
    path = save_csv_isi(name, record)

    # 展示
    st.subheader("评分结果")
    st.write(f"**总分：{total}**")
    for k, v in choices.items():
        st.write(f"- {k}：{v}（{score_map[v]} 分）")

    # 下载按钮（在表单外，不会报错）
    with open(path, "rb") as f:
        st.download_button(
            label="📥 下载结果 CSV",
            data=f,
            file_name=os.path.basename(path),
            mime="text/csv"
        )
    st.success("问卷提交成功！")
    
import os, psycopg2

def save_sqlpub(record: dict):
    """把同一条记录写入 SQLpub 的 PostgreSQL"""
    dsn = {
        "host":     os.getenv("SQLPUB_HOST"),
        "port":     int(os.getenv("SQLPUB_PORT", 5432)),
        "dbname":   os.getenv("SQLPUB_DB"),
        "user":     os.getenv("SQLPUB_USER"),
        "password": os.getenv("SQLPUB_PWD"),
    }
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
    (%(name)s, %(ts)s,
     %(1a_opt)s, %(1a_score)s,
     %(1b_opt)s, %(1b_score)s,
     %(1c_opt)s, %(1c_score)s,
     %(2_opt)s,  %(2_score)s,
     %(3_opt)s,  %(3_score)s,
     %(4_opt)s,  %(4_score)s,
     %(5_opt)s,  %(5_score)s,
     %(total)s)
    """
    try:
        with psycopg2.connect(**dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {
                    "name": record["姓名"],
                    "ts":   record["时间戳"],
                    "1a_opt": record["1a. 入睡困难(选项)"],
                    "1a_score": record["1a. 入睡困难(分值)"],
                    "1b_opt": record["1b. 睡眠维持困难(选项)"],
                    "1b_score": record["1b. 睡眠维持困难(分值)"],
                    "1c_opt": record["1c. 早醒(选项)"],
                    "1c_score": record["1c. 早醒(分值)"],
                    "2_opt": record["2. 睡眠满意度(选项)"],
                    "2_score": record["2. 睡眠满意度(分值)"],
                    "3_opt": record["3. 日常功能影响(选项)"],
                    "3_score": record["3. 日常功能影响(分值)"],
                    "4_opt": record["4. 生活质量影响(选项)"],
                    "4_score": record["4. 生活质量影响(分值)"],
                    "5_opt": record["5. 担心程度(选项)"],
                    "5_score": record["5. 担心程度(分值)"],
                    "total": record["总分"]
                })
            conn.commit()
    except Exception as e:
        st.error("SQLpub 写入失败：" + str(e))
