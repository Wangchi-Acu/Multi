import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv, pymysql

# ---------- 1. 工具函数 ----------
def save_csv_sds(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['ts'].replace('/', '').replace(':', '').replace(' ', '')}_{name}_SDS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def save_sqlpub_sds(record: dict):
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
        INSERT INTO sds_record
        (name, ts,
         q1, q2, q3, q4, q5, q6, q7, q8, q9, q10,
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
def calculate_sds(answers):
    raw = sum(answers)
    std = int(raw * 1.25 + 0.5)
    return raw, std

# ---------- 3. Streamlit 页面 ----------
st.set_page_config(page_title="抑郁自评量表 (SDS)", layout="centered")
st.image("jsszyylogo.png", width=500)
st.markdown("""
<div style='color: #000000; padding: 2px; border-radius: 15px; text-align: left;'>
    <h1 style='font-size: 37px; margin: 0; font-weight: 700;'>江苏省中医院针灸科</h1>
    <h1 style='font-size: 32px; margin: -15px 0 0 0; font-weight: 600;'>失眠专病门诊</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("<h3 style='color:#555555;'>抑郁自评量表 (SDS) 在线问卷</h3>", unsafe_allow_html=True)

name = st.text_input("姓名")

questions = [
    "1.我觉得闷闷不乐，情绪低沉",
    "2.我觉得一天之中早晨最好",
    "3.我一阵阵哭出来或觉得想哭",
    "4.我晚上睡眠不好",
    "5.我吃得跟平常一样多",
    "6.我与异性密切接触时和以往一样感到愉快",
    "7.我发觉我的体重在下降",
    "8.我有便秘的苦恼",
    "9.我心跳比平时快",
    "10.我无缘无故地感到疲乏",
    "11.我的头脑跟平常一样清楚",
    "12.我觉得经常做的事情并没有困难",
    "13.我觉得不安而平静不下来",
    "14.我对将来抱有希望",
    "15.我比平常容易生气激动",
    "16.我觉得作出决定是容易的",
    "17.我觉得自己是个有用的人，有人需要我",
    "18.我的生活过得很有意思",
    "19我认为如果我死了别人会生活得好些",
    "20.平常感兴趣的事我仍然照样感兴趣"
]

opts = ["从无或偶尔","有时","经常","总是如此"]
score_map = {"从无或偶尔":1,"有时":2,"经常":3,"总是如此":4}
reverse_idx = {2,5,6,11,12,14,16,17,18,20}  # 1 开始

choices = {}
for i, q in enumerate(questions, 1):
    choices[f"q{i}"] = st.radio(f"{i}. {q}", opts, horizontal=True, key=f"sds_q{i}")

if st.button("提交 SDS"):
    if not name.strip():
        st.warning("请输入姓名")
        st.stop()

    answers = []
    for i in range(1, 21):
        val = score_map[choices[f"q{i}"]]
        answers.append(5 - val if i in reverse_idx else val)

    raw, std = calculate_sds(answers)

    # 构造与 SQL 占位符一致的记录
    record = {
        "name": name,
        "ts": datetime.now().strftime("%Y/%-m/%-d %H:%M:%S"),
        **{f"q{i}": v for i, v in enumerate(answers, 1)},
        "raw": raw,
        "std": std
    }

    path = save_csv_sds(name, record)
    save_sqlpub_sds(record)

    st.subheader("评分结果")
    st.write(f"**原始分：{raw}  |  标准分：{std}**")
    level = "无抑郁" if std < 53 else "轻度抑郁" if std < 63 else "中度抑郁" if std < 73 else "重度抑郁"
    st.info(f"结论：{level}")

    # 防刷新下载
    csv_bytes = pd.DataFrame([record]).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 下载结果 CSV",
        data=csv_bytes,
        file_name=os.path.basename(path),
        mime="text/csv",
        key="download_single_sds"
    )
    st.success("SDS 提交成功！")

# ---------- 4. 管理员查看 ----------
if st.checkbox("管理员：查看已提交记录（SDS）"):
    pwd = st.text_input("请输入管理员密码", type="password")
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
            df = pd.read_sql("SELECT * FROM sds_record ORDER BY created_at DESC", conn)
            conn.close()
            if df.empty:
                st.info("暂无数据")
            else:
                st.dataframe(df)
                csv_all = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 导出全部 CSV", csv_all, "sds_all.csv", "text/csv")
        except Exception as e:
            st.error("读取数据库失败：" + str(e))
    else:
        st.error("密码错误，无法查看数据")
