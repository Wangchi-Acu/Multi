import streamlit as st
import pandas as pd
import pymysql, os, io
from datetime import datetime

st.set_page_config(page_title="患者查询", layout="wide")
st.title("📋 量表结果查询")

# 初始化 session state
if 'query_submitted' not in st.session_state:
    st.session_state.query_submitted = False
if 'patient_name' not in st.session_state:
    st.session_state.patient_name = ""
if 'df_all' not in st.session_state:
    st.session_state.df_all = pd.DataFrame()

with st.form("query_form"):
    name, pwd = st.columns([3, 1])
    patient = name.text_input("姓名", value=st.session_state.patient_name).strip()
    password = pwd.text_input("管理员密码", type="password")
    submitted = st.form_submit_button("确认查询")

# 处理查询
if submitted and patient and password:
    if password.strip() != "10338":
        st.error("密码错误")
        st.stop()

    # ---------- 数据库查询 ----------
    try:
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
                # 明确指定需要的列，避免列名冲突
                columns_to_select = "id, name, ts, created_at"
                if tbl == "isi_record":
                    columns_to_select += ", total_score"
                elif tbl == "fss_record":
                    columns_to_select += ", total_score"
                elif tbl == "psqi_record":
                    columns_to_select += ", total_score"
                elif tbl == "sas_record":
                    columns_to_select += ", std_score"
                elif tbl == "sds_record":
                    columns_to_select += ", std_score"
                elif tbl == "has_record":
                    columns_to_select += ", total_score"
                
                df = pd.read_sql(
                    f"SELECT {columns_to_select} FROM {tbl} WHERE name=%(name)s ORDER BY created_at DESC",
                    conn,
                    params={"name": patient}
                )
                df["量表"] = tbl.replace("_record", "").upper()
                dfs.append(df)
            except Exception as e:
                st.warning(f"查询表 {tbl} 时出错: {str(e)}")
        conn.close()
        
        df_all = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        if df_all.empty:
            st.warning("该患者暂无记录")
            st.session_state.query_submitted = False
            st.session_state.patient_name = ""
            st.session_state.df_all = pd.DataFrame()
        else:
            # 保存查询结果到 session state
            st.session_state.query_submitted = True
            st.session_state.patient_name = patient
            st.session_state.df_all = df_all
            
    except Exception as e:
        st.error(f"数据库连接失败: {str(e)}")
        st.stop()

# 显示查询结果（如果有的话）
if st.session_state.query_submitted and not st.session_state.df_all.empty:
    df_all = st.session_state.df_all
    patient = st.session_state.patient_name
    
    # 分数+等级映射
    score_map = {
        "ISI": "total_score",
        "FSS": "total_score",
        "PSQI": "total_score",
        "SAS": "std_score",
        "SDS": "std_score",
        "HAS": "total_score"
    }
    
    # 确保所有量表都有对应的列名
    for scale, col in score_map.items():
        if col not in df_all.columns:
            df_all[col] = None  # 添加缺失的列

    grade_map = {
        "ISI": lambda x: "无失眠" if x < 8 else "轻度" if x < 15 else "中度" if x < 22 else "重度" if x is not None else "无数据",
        "FSS": lambda x: "正常" if x < 36 else "疲劳" if x is not None else "无数据",
        "PSQI": lambda x: "很好" if x <= 5 else "尚可" if x <= 10 else "一般" if x <= 15 else "很差" if x is not None else "无数据",
        "SAS": lambda x: "无焦虑" if x < 50 else "轻度" if x < 60 else "中度" if x < 70 else "重度" if x is not None else "无数据",
        "SDS": lambda x: "无抑郁" if x < 53 else "轻度" if x < 63 else "中度" if x < 73 else "重度" if x is not None else "无数据",
        "HAS": lambda x: "正常" if x <= 32 else "过度觉醒" if x is not None else "无数据"
    }

    st.subheader("📊 分数 & 等级")
    cols = st.columns(len(score_map))
    for c, (scale, col) in zip(cols, score_map.items()):
        df_scale = df_all[df_all["量表"] == scale]
        if not df_scale.empty and col in df_scale.columns and not df_scale[col].isnull().all():
            latest_record = df_scale.iloc[0]
            val = latest_record[col]
            grade = grade_map[scale](val)
            c.metric(scale, f"{val}", delta=grade)
        else:
            c.metric(scale, "无数据", delta="无记录")

    # 按量表分组显示所有记录
    st.subheader("📈 详细记录历史")
    
    # 按量表分组
    for scale in ["ISI", "FSS", "PSQI", "SAS", "SDS", "HAS"]:
        df_scale = df_all[df_all["量表"] == scale]
        if not df_scale.empty:
            st.markdown(f"### {scale} 量表记录")
            
            # 按时间排序（最新的在上面）
            df_scale = df_scale.sort_values("created_at", ascending=False)
            
            # 显示该量表的所有记录
            for _, row in df_scale.iterrows():
                col_score = score_map[scale]
                score_val = row[col_score] if col_score in row and pd.notnull(row[col_score]) else "无数据"
                
                # 格式化时间显示
                if pd.notnull(row["ts"]):
                    display_time = row["ts"]
                else:
                    display_time = row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(row["created_at"]) else "无时间"
                
                # 显示记录信息
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"📅 {display_time}")
                with col2:
                    st.write(f"💯 总分: {score_val}")
                with col3:
                    grade = grade_map[scale](score_val) if score_val != "无数据" else "无数据"
                    st.write(f"📊 等级: {grade}")
                
                # 下载按钮
                # 清理时间戳中的特殊字符
                ts_str = str(row["ts"]).replace("/", "").replace(":", "").replace(" ", "").replace("-", "") if pd.notnull(row["ts"]) else "无时间戳"
                csv_name = f"{ts_str}_{patient}_{row['量表']}.csv"
                
                try:
                    # 连接数据库查询完整记录（SELECT * 获取所有字段）
                    conn = pymysql.connect(
                        host=os.getenv("SQLPUB_HOST"),
                        port=int(os.getenv("SQLPUB_PORT", 3307)),
                        user=os.getenv("SQLPUB_USER"),
                        password=os.getenv("SQLPUB_PWD"),
                        database=os.getenv("SQLPUB_DB"),
                        charset="utf8mb4"
                    )
                    
                    # 根据量表名确定表名
                    table_name = f"{row['量表'].lower()}_record"
                    
                    # 查询该记录的完整数据
                    detail_df = pd.read_sql(
                        f"SELECT * FROM {table_name} WHERE id=%(id)s",
                        conn,
                        params={"id": row['id']}
                    )
                    conn.close()
                    
                    # 如果查询到数据，则使用完整数据生成CSV
                    if not detail_df.empty:
                        buf = io.BytesIO()
                        detail_df.to_csv(buf, index=False, encoding="utf-8-sig")
                        buf.seek(0)
                    else:
                        # 如果没有找到详细记录，回退到原来的单行数据
                        buf = io.BytesIO()
                        pd.DataFrame([row]).to_csv(buf, index=False, encoding="utf-8-sig")
                        buf.seek(0)
                        
                except Exception as e:
                    # 如果查询失败，回退到原来的单行数据
                    st.warning(f"获取详细记录失败: {str(e)}")
                    buf = io.BytesIO()
                    pd.DataFrame([row]).to_csv(buf, index=False, encoding="utf-8-sig")
                    buf.seek(0)
                
                st.download_button(
                    label=f"📥 下载此记录",
                    data=buf,
                    file_name=csv_name,
                    mime="text/csv",
                    key=f"{row['量表']}_{row['id']}_{row['created_at']}"
                )
                
                st.markdown("---")  # 分隔线
                
            st.markdown("<br>", unsafe_allow_html=True)  # 空行分隔不同量表

elif not st.session_state.query_submitted:
    st.info("请先输入患者姓名和管理员密码，再点击「确认查询」")
