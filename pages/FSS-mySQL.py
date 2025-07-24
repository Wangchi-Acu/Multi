import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv, pymysql

# ---------- 1. 工具函数 ----------
def save_csv_fss(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['时间戳']}_{name}_FSS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def save_sqlpub(record: dict):
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
        INSERT INTO fss_record
        (name, ts,
         q1, q2, q3, q4, q5, q6, q7, q8, q9,
         total_score)
        VALUES
        (%(name)s, %(ts)s,
         %(q1)s, %(q2)s, %(q3)s, %(q4)s, %(q5)s,
         %(q6)s, %(q7)s, %(q8)s, %(q9)s, %(total)s)
        """
        cur = conn.cursor()
        cur.execute(sql, {
            "name": record["姓名"],
            "ts":   record["时间戳"],
            "q1": record["当我感到疲劳时，我就什么事都不想做了(分值)"],
            "q2": record["锻炼让我感到疲劳(分值)"],
            "q3": record["我很容易疲劳(分值)"],
            "q4": record["疲劳影响我的体能(分值)"],
            "q5": record["疲劳带来频繁的不适(分值)"],
            "q6": record["疲劳使我不能保持体能(分值)"],
            "q7": record["疲劳影响我从事某些工作(分值)"],
            "q8": record["疲劳是最影响我活动能力的症状之一(分值)"],
            "q9": record["疲劳影响了我的工作、家庭、社会活动(分值)"],
            "total": record["总分"]
        })
        conn.commit()
    except Exception as e:
        st.error("SQLpub 写入失败：" + str(e))
    finally:
        if 'conn' in locals():
            conn.close()

# ---------- 2. 页面 ----------
st.set_page_config(page_title="疲劳严重程度量表（FSS）", layout="centered")
st.image("jsszyylogo.png", width=500)
st.title("江苏省中医院针灸科失眠专病门诊")
st.markdown("<h3 style='color:#555555;'>疲劳严重程度量表（FSS）在线问卷</h3>", unsafe_allow_html=True)
st.markdown("> 请根据自己的真实体验和实际情况来回答，不需要花费太多时间去思考。")
st.markdown("> 1 分 = 非常不同意，7 分 = 非常同意。")

name = st.text_input("姓名")

questions = [
    "当我感到疲劳时，我就什么事都不想做了",
    "锻炼让我感到疲劳",
    "我很容易疲劳",
    "疲劳影响我的体能",
    "疲劳带来频繁的不适",
    "疲劳使我不能保持体能",
    "疲劳影响我从事某些工作",
    "疲劳是最影响我活动能力的症状之一",
    "疲劳影响了我的工作、家庭、社会活动"
]

choices = {}
for i, q in enumerate(questions, 1):
    choices[q] = st.radio(
        f"{i}. {q}",
        options=range(1, 8),
        horizontal=True,
        format_func=lambda x: f"{x} 分",
        key=f"fss_q{i}"
    )

if st.button("提交 FSS"):
    if not name:
        st.warning("请输入姓名")
        st.stop()

    record = {
    "姓名": name,
    "时间戳": datetime.now().strftime("%Y/%-m/%-d %H:%M:%S")   # 例如 2025/7/24 16:24:49
}
    total = 0
    for q, score in choices.items():
        record[f"{q}(分值)"] = score
        total += score
    record["总分"] = total

    path = save_csv_fss(name, record)
    save_sqlpub(record)

    st.subheader("评分结果")
    st.write(f"**总分：{total}**")
    level = "正常" if total < 36 else "需进一步评估"
    st.info(f"结论：{level}")

    csv_bytes = pd.DataFrame([record]).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 下载结果 CSV",
        data=csv_bytes,
        file_name=os.path.basename(path),
        mime="text/csv",
        key="download_single_fss"
    )
    st.success("FSS 提交成功！")

# ---------- 3. 管理员查看 ----------
if st.checkbox("管理员：查看已提交记录（FSS）"):
    pwd = st.text_input("请输入管理员密码", type="password")
    if pwd:
        if pwd.strip() == "12024168":
            try:
                conn = pymysql.connect(
                    host=os.getenv("SQLPUB_HOST"),
                    port=int(os.getenv("SQLPUB_PORT", 3307)),
                    user=os.getenv("SQLPUB_USER"),
                    password=os.getenv("SQLPUB_PWD"),
                    database=os.getenv("SQLPUB_DB"),
                    charset="utf8mb4"
                )
                df = pd.read_sql("SELECT * FROM fss_record ORDER BY created_at DESC", conn)
                df['ts'] = df['ts'].astype(str).str.zfill(12)
                conn.close()
                st.dataframe(df)
                csv_all = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 导出全部 CSV", csv_all, "fss_all.csv", "text/csv")
            except Exception as e:
                st.error("读取数据库失败：" + str(e))
        else:
            st.error("密码错误，无法查看数据")
