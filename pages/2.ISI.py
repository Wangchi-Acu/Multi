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
