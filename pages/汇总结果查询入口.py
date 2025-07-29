import streamlit as st
import pandas as pd
import pymysql
import os
import io
from datetime import datetime

st.set_page_config(page_title="患者查询", layout="wide")
st.title("📋 患者量表查询与下载")

# 确认密码
pwd = st.text_input("请输入管理员密码", type="password")
if not st.button("确认密码"):
    st.stop()
if pwd.strip() != "12024168":
    st.error("密码错误")
    st.stop()

# 输入患者姓名
patient = st.text_input("请输入患者姓名").strip()
if not patient:
    st.warning("请输入患者姓名")
    st.stop()

# 连接数据库
conn = pymysql.connect(
    host=os.getenv("SQLPUB_HOST"),
    port=int(os.getenv("SQLPUB_PORT", 3307)),
    user=os.getenv("SQLPUB_USER"),
    password=os.getenv("SQLPUB_PWD"),
    database=os.getenv("SQLPUB_DB"),
    charset="utf8mb4"
)

# 查询函数
def query_patient(patient_name):
    tables = ["isi_record", "fss_record", "psqi_record", "sas_record", "sds_record", "has_record"]
    dfs = []
    for tbl in tables:
        try:
            df = pd.read_sql(
                f"SELECT * FROM {tbl} WHERE name=%s ORDER BY created_at DESC",
                conn,
                params={"name": patient_name}
            )
            df["量表"] = tbl.replace("_record", "").upper()
            dfs.append(df)
        except Exception as e:
            st.error(f"查询 {tbl} 表时出错：{e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = query_patient(patient)
conn.close()  # 关闭数据库连接

if df.empty:
    st.info("该患者暂无记录")
else:
    # 汇总总分
    score_map = {
        "ISI": "total",
        "FSS": "total_score",
        "PSQI": "total_score",
        "SAS": "std_score",
        "SDS": "std_score",
        "HAS": "total_score"
    }
    summary = {}
    for scale in score_map:
        col = score_map[scale]
        if col in df.columns:
            latest = df[df["量表"] == scale][col].values[0] if not df[df["量表"] == scale].empty else None
            summary[scale] = latest

    st.subheader("📊 总分汇总")
    if summary:
        cols = st.columns(len(summary))
        for c, (scale, val) in zip(cols, summary.items()):
            c.metric(scale, val)
    else:
        st.info("暂无总分数据")

    # 列表及下载
    st.subheader("📈 详细记录")
    for _, row in df.iterrows():
        scale = row["量表"]
        ts_str = str(row["ts"]).replace("/", "").replace(":", "").replace(" ", "")
        csv_name = f"{ts_str}_{patient}_{scale}.csv"

        # 单行 DataFrame → CSV bytes
        buf = io.BytesIO()
        pd.DataFrame([row]).to_csv(buf, index=False, encoding="utf-8-sig")
        buf.seek(0)

        st.download_button(
            label=f"📥 下载 {scale} 记录 ({row['ts']})",
            data=buf,
            file_name=csv_name,
            mime="text/csv",
            key=f"{scale}_{row['id']}"
        )

    # 一键合并下载全部 CSV
    if st.button("📦 一键合并下载全部 CSV"):
        buf_all = io.BytesIO()
        df.to_csv(buf_all, index=False, encoding="utf-8-sig")
        buf_all.seek(0)
        st.download_button(
            label="📦 合并 CSV",
            data=buf_all,
            file_name=f"{patient}_all_records.csv",
            mime="text/csv"
        )
