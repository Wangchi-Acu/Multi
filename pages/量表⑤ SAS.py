import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv, pymysql

# ---------- 1. 工具函数 ----------
def save_csv_sas(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['ts'].replace('/', '').replace(':', '').replace(' ', '')}_{name}_SAS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def save_sqlpub_sas(record: dict):
    try:
        conn = pymysql.connect(
            host=os.getenv("SQLPUB_HOST"),
            port=int(os.getenv("SQLPUB_PORT", 3307)),
            user=os.getenv("SQLPUB_USER"),
            password=os.getenv("SQLPUB_PWD"),
            database=os.getenv("SQLPUB_DB"),
            charset="utf8mb4",
            connect_timeout=5
        )
        sql = """
        INSERT INTO sas_record
        (name, ts, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10,
         q11, q12, q13, q14, q15, q16, q17, q18, q19, q20,
         raw_score, std_score)
        VALUES
        (%(name)s, %(ts)s,
         %(q1)s, %(q2)s, %(q3)s, %(q4)s, %(q5)s,
         %(q6)s, %(q7)s, %(q8)s, %(q9)s, %(q10)s,
         %(q11)s, %(q12)s, %(q13)s, %(q14)s, %(q15)s,
         %(q16)s, %(q17)s, %(q18)s, %(q19)s, %(q20)s,
         %(raw)s, %(std)s)
        """
        cur = conn.cursor()
        cur.execute(sql, record)
        conn.commit()
    except Exception as e:
        st.error("SQLpub 写入失败：" + str(e))
    finally:
        if 'conn' in locals():
            conn.close()

# ---------- 2. 计算函数 ----------
def calculate_sas(answers):
    # answers: 20 个原始分
    raw = sum(answers)
    std = int(raw * 1.25 + 0.5)
    return raw, std

# ---------- 3. Streamlit 页面 ----------
st.set_page_config(page_title="焦虑自评量表（SAS）", layout="centered")
st.image("jsszyylogo.png", width=500)
st.markdown("""
<div style='color: #000000; padding: 2px; border-radius: 15px; text-align: left;'>
    <h1 style='font-size: 37px; margin: 0; font-weight: 700;'>江苏省中医院针灸科</h1>
    <h1 style='font-size: 32px; margin: -15px 0 0 0; font-weight: 600;'>失眠专病门诊</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("<h3 style='color:#555555;'>焦虑自评量表（SAS）在线问卷</h3>", unsafe_allow_html=True)

name = st.text_input("姓名")

questions = [
    "1.我觉得比平常容易紧张和着急",
    "2.我无缘无故地感到害怕",
    "3.我容易心里烦乱或觉得惊恐",
    "4.我觉得我可能将要发疯",
    "5.我觉得一切都很好，也不会发生什么不幸",
    "6.我手脚发抖打颤",
    "7.我因为头痛、颈痛和背痛而苦恼",
    "8.我感觉容易衰弱和疲乏",
    "9.我觉得心平气和，并且容易安静地坐着",
    "10.我觉得心跳得很快",
    "11.我因为一阵阵头晕而苦恼",
    "12.我有晕倒发作或觉得要晕倒似的",
    "13.我吸气呼气都感到很容易",
    "14.我的手脚麻木和刺痛",
    "15.我因为胃痛和消化不良而苦恼",
    "16.我常常要小便",
    "17.我的手常常是干燥温暖的",
    "18.我脸红发热",
    "19.我容易入睡并且一夜睡得很好",
    "20.我做噩梦"
]

opts = ["从无或偶尔","有时","经常","总是如此"]
score_map = {"从无或偶尔":1,"有时":2,"经常":3,"总是如此":4}
reverse_idx = {4,9,13,17,19}  # 1 开始

choices = {}
for i, q in enumerate(questions, 1):
    choices[f"q{i}"] = st.radio(
        f"{i}. {q}",
        options=opts,
        horizontal=True,
        key=f"sas_q{i}"
    )

if st.button("提交 SAS"):
    if not name.strip():
        st.warning("请输入姓名")
        st.stop()

    answers = []
    for i in range(1, 21):
        val = score_map[choices[f"q{i}"]]
        answers.append(5 - val if i in reverse_idx else val)

    raw, std = calculate_sas(answers)

    # 构造与 SQL 占位符完全一致的记录
    record = {
        "name": name,
        "ts": datetime.now().strftime("%Y/%-m/%-d %H:%M:%S"),
        **{f"q{i}": v for i, v in enumerate(answers, 1)},
        "raw": raw,
        "std": std
    }

    path = save_csv_sas(name, record)
    save_sqlpub_sas(record)

    st.subheader("评分结果")
    st.write(f"**原始分：{raw}  |  标准分：{std}**")
    level = "无焦虑" if std < 50 else "轻度焦虑" if std < 60 else "中度焦虑" if std < 70 else "重度焦虑"
    st.info(f"结论：{level}")

    st.success("SAS 提交成功！")
