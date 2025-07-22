import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

# ---------- 保存函数 ----------
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

# ---------- Streamlit 界面 ----------
st.set_page_config(page_title="疲劳严重程度量表（FSS）", layout="centered")
st.image("jsszyylogo.png", width=500)  # 更改url_to_your_logo.png为你的logo图片链接，调整width为适当的大小
st.title("江苏省中医院针灸科失眠专病门诊")
st.markdown(
    "<h3 style='color:#555555;'>疲劳严重程度量表（FSS）在线问卷</h3>",
    unsafe_allow_html=True
)
st.markdown("> 请根据自己的真实体验和实际情况来回答，不需要花费太多的时间去思考。")
st.markdown("> 自1分至7分为非常不同意逐渐过渡为非常同意。")

# ---------- 页面 ----------
def show_fss():

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
        st.write(f"{i}. {q}")
        choices[q] = st.radio(
            label="",
            options=list(range(1, 8)),          # 1–7 分
            horizontal=True,
            format_func=lambda x: f"{x} 分",
            key=f"fss_{i}"
        )
    if st.button("提交 FSS"):
        if not name:
            st.warning("请输入姓名")
            st.stop()

        record = {"姓名": name, "时间戳": datetime.now().strftime("%Y%m%d%H%M")}
        total = 0
        for q, score in choices.items():
            record[f"{q}(分值)"] = score
            total += score
        record["总分"] = total

        path = save_csv_fss(name, record)

        st.subheader("评分结果")
        st.write(f"**总分：{total}**")
        level = "正常" if total < 36 else "需进一步评估"
        st.info(f"结论：{level}")

        with open(path, "rb") as f:
            st.download_button(
                label="📥 下载结果 CSV",
                data=f,
                file_name=os.path.basename(path),
                mime="text/csv"
            )
        st.success("FSS 提交成功！")

if __name__ == "__main__":
    show_fss()
