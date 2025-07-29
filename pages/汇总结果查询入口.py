import streamlit as st
import pandas as pd
import pymysql, os, io
from datetime import datetime

st.set_page_config(page_title="患者查询", layout="wide")
st.title("📋 患者量表查询")

with st.form("query_form"):
    name, pwd = st.columns([3, 1])
    patient = name.text_input("患者姓名").strip()
    password = pwd.text_input("管理员密码", type="password")
    submitted = st.form_submit_button("确认查询")

if submitted and patient and password:
    if password.strip() != "12024168":
        st.error("密码错误")
        st.stop()

    # ---------- 数据库查询（核心部分）----------
    conn = pymysql.connect(
        host=os.getenv("SQLPUB_HOST"),
        port=int(os.getenv("SQLPUB_PORT", 3307)),
        user=os.getenv("SQLPUB_USER"),
        password=os.getenv("SQLPUB_PWD"),
        database=os.getenv("SQLPUB_DB"),
        charset="utf8mb4"
    )
    
    tables = ["isi_record", "fss_record", "psqi_record", "sas_record", "sds_record", "has_record"]
    dfs = []
    for tbl in tables:
        try:
            df = pd.read_sql(
                f"SELECT * FROM {tbl} WHERE name=%(name)s ORDER BY created_at DESC",
                conn,
                params={"name": patient}
            )
            df["量表"] = tbl.replace("_record", "").upper()
            dfs.append(df)
        except Exception as e:
            st.warning(f"查询表 {tbl} 时出错: {str(e)}")
    conn.close()
    
    df_all = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    # ---------- 查询结束 ----------

    if df_all.empty:
        st.warning("该患者暂无记录")
        st.stop()

    # 分数+等级映射
    score_map = {
        "ISI": "total",
        "FSS": "total_score",
        "PSQI": "total_score",
        "SAS": "std_score",
        "SDS": "std_score",
        "HAS": "total_score"
    }
    grade_map = {
        "ISI": lambda x: "无失眠" if x < 8 else "轻度" if x < 15 else "中度" if x < 22 else "重度",
        "FSS": lambda x: "正常" if x < 36 else "疲劳",
        "PSQI": lambda x: "很好" if x <= 5 else "尚可" if x <= 10 else "一般" if x <= 15 else "很差",
        "SAS": lambda x: "无焦虑" if x < 50 else "轻度" if x < 60 else "中度" if x < 70 else "重度",
        "SDS": lambda x: "无抑郁" if x < 53 else "轻度" if x < 63 else "中度" if x < 73 else "重度",
        "HAS": lambda x: "正常" if x <= 32 else "过度觉醒"
    }

    st.subheader("📊 分数 & 等级")
    cols = st.columns(len(score_map))
    for c, (scale, col) in zip(cols, score_map.items()):
        df_scale = df_all[df_all["量表"] == scale]
        if not df_scale.empty:
            latest_record = df_scale.iloc[0]
            val = latest_record[col]
            grade = grade_map[scale](val)
            c.metric(scale, f"{val}", delta=grade)
        else:
            c.metric(scale, "无数据", delta="无记录")

    # 下载按钮
    st.subheader("📈 详细记录")
    for _, row in df_all.iterrows():
        # 清理时间戳中的特殊字符
        ts_str = str(row["ts"]).replace("/", "").replace(":", "").replace(" ", "")
        csv_name = f"{ts_str}_{patient}_{row['量表']}.csv"
        
        buf = io.BytesIO()
        pd.DataFrame([row]).to_csv(buf, index=False, encoding="utf-8-sig")
        buf.seek(0)
        
        st.download_button(
            label=f"📥 下载 {row['量表']} 记录 ({row['ts']})",
            data=buf,
            file_name=csv_name,
            mime="text/csv",
            key=f"{row['量表']}_{row['id']}"
        )

    # 一键合并下载
    if st.button("📦 一键合并下载全部记录"):
        buf_all = io.BytesIO()
        df_all.to_csv(buf_all, index=False, encoding="utf-8-sig")
        buf_all.seek(0)
        
        current_time = datetime.now().strftime("%Y%m%d%H%M")
        filename = f"{patient}_全部量表记录_{current_time}.csv"
        
        st.download_button(
            label="📦 合并 CSV",
            data=buf_all,
            file_name=filename,
            mime="text/csv"
        )
else:
    st.info("请先输入患者姓名和管理员密码，再点击「确认查询」")
