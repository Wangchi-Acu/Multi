import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv, pymysql

# ---------- 1. 工具函数 ----------
def save_csv_has(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['ts'].replace('/', '').replace(':', '').replace(' ', '')}_{name}_HAS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def save_sqlpub_has(record: dict):
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
        INSERT INTO has_record
        (name, ts,
         q1, q2, q3, q4, q5, q6, q7, q8, q9, q10,
         q11, q12, q13, q14, q15, q16, q17, q18, q19, q20,
         q21, q22, q23, q24, q25, q26,
         total_score)
        VALUES
        (%(name)s, %(ts)s,
         %(q1)s, %(q2)s, %(q3)s, %(q4)s, %(q5)s, %(q6)s, %(q7)s, %(q8)s, %(q9)s, %(q10)s,
         %(q11)s, %(q12)s, %(q13)s, %(q14)s, %(q15)s, %(q16)s, %(q17)s, %(q18)s, %(q19)s, %(q20)s,
         %(q21)s, %(q22)s, %(q23)s, %(q24)s, %(q25)s, %(q26)s,
         %(total)s)
        """
        cur = conn.cursor()
        cur.execute(sql, record)
        conn.commit()
    except Exception as e:
        st.error("SQLpub 写入失败：" + str(e))
    finally:
        if 'conn' in locals():
            conn.close()

# ---------- 2. Streamlit 页面 ----------
st.set_page_config(page_title="过度觉醒量表（HAS）", layout="centered")
st.image("jsszyylogo.png", width=500)
st.markdown("""
<div style='color: #000000; padding: 2px; border-radius: 15px; text-align: left;'>
    <h1 style='font-size: 37px; margin: 0; font-weight: 700;'>江苏省中医院针灸科</h1>
    <h1 style='font-size: 32px; margin: -15px 0 0 0; font-weight: 600;'>失眠专病门诊</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("<h3 style='color:#555555;'>过度觉醒量表（HAS）在线问卷</h3>", unsafe_allow_html=True)

name = st.text_input("姓名")

questions = [
    "1. 我很有条理",
    "2. 我早晨不容易醒来",
    "3. 我工作非常细心",
    "4. 我总是控制不住的胡思乱想",
    "5. 对于自己的感情和感受，我总会在意很多",
    "6. 明亮的灯光、拥挤的人群、嘈杂的噪音或拥挤的交通让我心烦意乱",
    "7. 我在晚上状态最好",
    "8. 我无法午睡，怎么想办法也睡不着",
    "9. 我往往会预想有可能发生的麻烦",
    "10. 我的卧室一团乱",
    "11. 我总觉得处处被针对",
    "12. 当很多事情一起发生的时候我会很紧张",
    "13. 我善于处理细枝末节",
    "14. 我入睡困难",
    "15. 我处事小心谨慎",
    "16. 晚上躺在床上时，我也一直在想各种各样的事",
    "17. 突然的、巨大的噪音会让我久久不能平静",
    "18. 我认真的有些过分",
    "19. 咖啡因（茶叶）会对我产生严重的不良作用",
    "20. 当事情不顺时，我往往会感到沮丧",
    "21. 我的生活千篇一律，没有新意",
    "22. 我的脑海里总是重复某些想法",
    "23. 我要花很长时间才能下决心",
    "24. 酒精让我昏昏欲睡",
    "25. 我很容易流泪",
    "26. 某些事情发生后很久之后，我还念念不忘"
]

opts = ["从来不","偶尔有","经常有","绝大部分时间有"]
score_map = {"从来不":0,"偶尔有":1,"经常有":2,"绝大部分时间有":3}

choices = {}
for i, q in enumerate(questions, 1):
    choices[f"q{i}"] = st.radio(f"{i}. {q}", opts, horizontal=True, key=f"has_q{i}")

if st.button("提交 HAS"):
    if not name.strip():
        st.warning("请输入姓名")
        st.stop()

    answers = [score_map[choices[f"q{i}"]] for i in range(1, 27)]
    total = sum(answers)

    # 构造与 SQL 占位符完全一致的记录
    record = {
        "name": name,
        "ts": datetime.now().strftime("%Y/%-m/%-d %H:%M:%S"),
        **{f"q{i}": v for i, v in enumerate(answers, 1)},
        "total": total
    }

    path = save_csv_has(name, record)
    save_sqlpub_has(record)

    st.subheader("评分结果")
    st.write(f"**总分：{total}**")
    level = "正常" if total <= 32 else "过度觉醒"
    st.info(f"结论：{level}")

    # 防刷新下载
    csv_bytes = pd.DataFrame([record]).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 下载结果 CSV",
        data=csv_bytes,
        file_name=os.path.basename(path),
        mime="text/csv",
        key="download_single_has"
    )
    st.success("HAS 提交成功！")

# ---------- 4. 管理员查看 ----------
if st.checkbox("管理员：查看已提交记录（HAS）"):
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
            df = pd.read_sql("SELECT * FROM has_record ORDER BY created_at DESC", conn)
            conn.close()
            if df.empty:
                st.info("暂无数据")
            else:
                st.dataframe(df)
                csv_all = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 导出全部 CSV", csv_all, "has_all.csv", "text/csv")
        except Exception as e:
            st.error("读取数据库失败：" + str(e))
    else:
        st.error("密码错误，无法查看数据")
