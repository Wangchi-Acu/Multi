import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv, pymysql
import altair as alt

# ---------- 1. 工具函数 ----------
def save_csv_psqi(name, record):
    save_dir = r"F:\网页量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['ts'].replace('/', '').replace(':', '').replace(' ', '')}_{name}_PSQI.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def save_sqlpub_psqi(record: dict):
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
        INSERT INTO psqi_record
        (name, gender, ts, age, height, weight, contact,
         bed_time, getup_time, sleep_latency_choice, sleep_duration_choice,
         q5a, q5b, q5c, q5d, q5e, q5f, q5g, q5h, q5i, q5j,
         q6, q7, q8, q9,
         A, B, C, D, E, F, G, total_score, sleep_efficiency)
        VALUES
        (%(name)s, %(gender)s, %(ts)s, %(age)s, %(height)s, %(weight)s, %(contact)s,
         %(bed_time)s, %(getup_time)s, %(sleep_latency_choice)s, %(sleep_duration_choice)s,
         %(q5a)s, %(q5b)s, %(q5c)s, %(q5d)s, %(q5e)s, %(q5f)s, %(q5g)s, %(q5h)s, %(q5i)s, %(q5j)s,
         %(q6)s, %(q7)s, %(q8)s, %(q9)s,
         %(A)s, %(B)s, %(C)s, %(D)s, %(E)s, %(F)s, %(G)s, %(total)s, %(sleep_efficiency)s)
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
def calculate_sleep_efficiency(bed, getup, choice):
    try:
        bed_t  = datetime.strptime(bed,  "%H:%M").time()
        get_t  = datetime.strptime(getup, "%H:%M").time()
        bed_dt = datetime(2000, 1, 1, bed_t.hour, bed_t.minute)
        get_dt = datetime(2000, 1, 2 if get_t < bed_t else 1, get_t.hour, get_t.minute)
        bed_d  = (get_dt - bed_dt).total_seconds() / 3600
        dur_map = {1: 7.5, 2: 6.5, 3: 5.5, 4: 4.5}
        actual  = dur_map.get(choice, 0)
        return (actual / bed_d * 100) if bed_d else 0
    except:
        return 0

def get_component_score(eff):
    return 0 if eff > 85 else 1 if 75 <= eff <= 84 else 2 if 65 <= eff <= 74 else 3

def calculate_psqi(data):
    A = data['q6'] - 1
    lat = data['sleep_latency_choice'] - 1
    q5a = data['q5a'] - 1
    B = 0 if lat+q5a==0 else (1 if lat+q5a<=2 else 2 if lat+q5a<=4 else 3)
    C = data['sleep_duration_choice'] - 1
    eff = calculate_sleep_efficiency(data['bed_time'], data['getup_time'], data['sleep_duration_choice'])
    D = get_component_score(eff)
    E_items = ['q5a','q5b','q5c','q5d','q5e','q5f','q5g','q5h','q5i','q5j']
    E_score = sum(data[k]-1 for k in E_items)
    E = 0 if E_score==0 else 1 if E_score<=9 else 2 if E_score<=18 else 3
    F = data['q7'] - 1
    G_total = (data['q8']-1)+(data['q9']-1)
    G = 0 if G_total==0 else 1 if G_total<=2 else 2 if G_total<=4 else 3
    total = A+B+C+D+E+F+G
    return {'A':A,'B':B,'C':C,'D':D,'E':E,'F':F,'G':G,'total':total,'sleep_efficiency':eff}

# ---------- 3. Streamlit 页面 ----------
st.set_page_config(page_title="匹兹堡睡眠质量指数(PSQI)", layout="centered")
st.image("jsszyylogo.png", width=500)
st.markdown("""
<div style='background: linear-gradient(135deg,#e3f2fd 0%,#bbdefb 100%); color: #0d47a1; padding: 25px; border-radius: 15px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
    <h1 style='font-size: 32px; margin: 0; font-weight: 700;'>江苏省中医院针灸科</h1>
    <h1 style='font-size: 32px; margin: 5px 0 0 0; font-weight: 600;'>失眠专病门诊</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("<h3 style='color:#555555;'>匹兹堡睡眠质量指数（PSQI）在线问卷</h3>", unsafe_allow_html=True)
st.markdown("> 请根据 **最近一个月** 的实际情况填写")

with st.form("psqi_form"):
    st.subheader("① 基本信息")
    name   = st.text_input("姓名")
    gender = st.selectbox("性别", ["男", "女", "其他"])
    age    = st.number_input("年龄", 1, 120, 25)
    height = st.number_input("身高(cm)", 50, 250, 170)
    weight = st.number_input("体重(kg)", 20, 200, 65)
    contact= st.text_input("联系方式")

    st.subheader("② 睡眠习惯")
    bed   = st.text_input("晚上上床时间 (HH:MM)", value="23:30")
    getup = st.text_input("早上起床时间 (HH:MM)", value="07:00")
    latency = st.selectbox("入睡所需时间", ["≤15分钟","16-30分钟","31-60分钟","≥60分钟"], index=1)
    duration = st.number_input("实际睡眠时长（小时）", 0.0, 24.0, 6.5, 0.1, format="%.1f")

    st.subheader("③ 睡眠问题（每周发生频率）")
    opts = ["没有","少于1次","1-2次","3次以上"]
    q5a = st.selectbox("5a. 入睡困难", opts, index=0)
    q5b = st.selectbox("5b. 夜间易醒或早醒", opts, index=0)
    q5c = st.selectbox("5c. 夜间去厕所", opts, index=0)
    q5d = st.selectbox("5d. 呼吸不畅", opts, index=0)
    q5e = st.selectbox("5e. 咳嗽或鼾声高", opts, index=0)
    q5f = st.selectbox("5f. 感觉冷", opts, index=0)
    q5g = st.selectbox("5g. 感觉热", opts, index=0)
    q5h = st.selectbox("5h. 做恶梦", opts, index=0)
    q5i = st.selectbox("5i. 疼痛不适", opts, index=0)
    q5j = st.selectbox("5j. 其他影响", opts, index=0)

    st.subheader("④ 其他")
    q6 = st.selectbox("总体睡眠质量", ["很好","较好","较差","很差"], index=1)
    q7 = st.selectbox("使用催眠药物（每周发生频率）", ["没有","少于1次","1-2次","3次以上"], index=0)
    q8 = st.selectbox("白天困倦（每周发生频率）", ["没有","少于1次","1-2次","3次以上"], index=0)
    q9 = st.selectbox("精力不足（每周发生频率）", ["没有","少于1次","1-2次","3次以上"], index=0)

    submitted = st.form_submit_button("提交问卷")

if submitted:
    if not name.strip():
        st.warning("请输入姓名")
        st.stop()

    # 数据整理
    data = {
        "name": name, "gender": gender,
        "age": age, "height": height, "weight": weight, "contact": contact,
        "bed_time": bed, "getup_time": getup,
        "sleep_latency_choice":["≤15分钟","16-30分钟","31-60分钟","≥60分钟"].index(latency)+1,
        "sleep_duration_choice": 1 if duration>7 else 2 if 6<=duration<=7 else 3 if 5<=duration<6 else 4,
        **{f"q5{k}":opts.index(v)+1 for k,v in zip("abcdefghij",[q5a,q5b,q5c,q5d,q5e,q5f,q5g,q5h,q5i,q5j])},
        "q6":["很好","较好","较差","很差"].index(q6)+1,
        "q7":opts.index(q7)+1,"q8":opts.index(q8)+1,"q9":opts.index(q9)+1
    }
    res = calculate_psqi(data)

    # 构造记录（键名务必与 SQL 占位符一致）
    record = {
        "name": name,
        "gender": gender,
        "ts": datetime.now().strftime("%Y/%-m/%-d %H:%M:%S"),
        "age": age, "height": height, "weight": weight, "contact": contact,
        "bed_time": bed, "getup_time": getup,
        "sleep_latency_choice": data["sleep_latency_choice"],
        "sleep_duration_choice": data["sleep_duration_choice"],
        **{f"q5{k}": data[f"q5{k}"] for k in "abcdefghij"},
        "q6": data["q6"], "q7": data["q7"], "q8": data["q8"], "q9": data["q9"],
        **res
    }
    path = save_csv_psqi(name, record)
    save_sqlpub_psqi(record)

    # 结果展示
    st.subheader("📊 各成分得分")
    score_df = pd.DataFrame({
        "成分": ["A 睡眠质量", "B 入睡时间", "C 睡眠时间",
                 "D 睡眠效率", "E 睡眠障碍", "F 催眠药物", "G 日间功能"],
        "得分": [res[k] for k in "ABCDEFG"]
    })
    st.dataframe(score_df, use_container_width=True)

    chart = alt.Chart(score_df).mark_bar().encode(
        x="成分",
        y="得分",
        color=alt.Color("成分", scale=alt.Scale(domain=score_df["成分"],
                                             range=["#FF595E","#FFCA3A","#8AC926",
                                                    "#1982C4","#6A4C93","#FF924C","#52A675"]))
    ).properties(height=350)
    st.altair_chart(chart, use_container_width=True)

    level = "尚可" if res["total"] <= 5 else "一般" if res["total"] <= 10 else "较差" if res["total"] <= 15 else "很差"
    st.metric("🎯 PSQI 总分", f"{res['total']} 分")
    st.info(f"综合评定：睡眠质量 **{level}**")

    # 防刷新下载
    csv_bytes = pd.DataFrame([record]).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 下载结果 CSV",
        data=csv_bytes,
        file_name=os.path.basename(path),
        mime="text/csv",
        key="download_single_psqi"
    )
    st.success("PSQI 提交成功！")

# ---------- 4. 管理员查看 ----------
if st.checkbox("管理员：查看已提交记录（PSQI）"):
    pwd = st.text_input("请输入管理员密码", type="password")
    if st.button("确认密码"):
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
                df = pd.read_sql("SELECT * FROM psqi_record ORDER BY created_at DESC", conn)
                conn.close()
                if df.empty:
                    st.info("暂无数据")
                else:
                    st.dataframe(df)
                    csv_all = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button("📥 导出全部 CSV", csv_all, "psqi_all.csv", "text/csv")
            except Exception as e:
                st.error("读取数据库失败：" + str(e))
        else:
            st.error("密码错误，无法查看数据")
