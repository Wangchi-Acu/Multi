import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv

def save_csv_sas(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['时间戳']}_{name}_SAS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def show_sas():
    st.set_page_config(page_title="SAS 焦虑量表")
    st.title("焦虑自评量表 SAS")

    name = st.text_input("姓名")

    questions = [
        "我觉得比平常容易紧张和着急",
        "我无缘无故地感到害怕",
        "我容易心里烦乱或觉得惊恐",
        "我觉得我可能将要发疯",
        "我觉得一切都很好，也不会发生什么不幸（反向）",
        "我手脚发抖打颤",
        "我因为头痛、颈痛和背痛而苦恼",
        "我感觉容易衰弱和疲乏",
        "我觉得心平气和，并且容易安静地坐着（反向）",
        "我觉得心跳得很快",
        "我因为一阵阵头晕而苦恼",
        "我有晕倒发作或觉得要晕倒似的",
        "我吸气呼气都感到很容易（反向）",
        "我的手脚麻木和刺痛",
        "我因为胃痛和消化不良而苦恼",
        "我常常要小便",
        "我的手常常是干燥温暖的（反向）",
        "我脸红发热",
        "我容易入睡并且一夜睡得很好（反向）",
        "我做噩梦"
    ]

    opts = ["从无或偶尔","有时","经常","总是如此"]
    score_map = {"从无或偶尔":1,"有时":2,"经常":3,"总是如此":4}
    reverse_idx = {4,8,12,16,18}  # 0 开始

    choices = {}
    for i, q in enumerate(questions, 1):
        st.write(f"{i}. {q}")
        choices[q] = st.radio(label="", options=opts, horizontal=True, key=f"sas_{i}")

    if st.button("提交 SAS"):
        if not name:
            st.warning("请输入姓名")
            st.stop()

        record = {"姓名": name, "时间戳": datetime.now().strftime("%Y%m%d%H%M")}
        raw = 0
        for i, (q, opt) in enumerate(choices.items()):
            val = score_map[opt]
            record[f"{q}(选项)"] = opt
            record[f"{q}(分值)"] = 5 - val if i in reverse_idx else val
            raw += record[f"{q}(分值)"]
        std = int(raw * 1.25 + 0.5)
        record["总分(原始分)"] = raw
        record["标准分"] = std

        path = save_csv_sas(name, record)

        st.subheader("评分结果")
        st.write(f"**原始分：{raw}  |  标准分：{std}**")
        level = "无焦虑" if std < 50 else "轻度焦虑" if std < 60 else "中度焦虑" if std < 70 else "重度焦虑"
        st.info(f"结论：{level}")

        with open(path, "rb") as f:
            st.download_button(
                label="📥 下载结果 CSV",
                data=f,
                file_name=os.path.basename(path),
                mime="text/csv"
            )
        st.success("SAS 提交成功！")

if __name__ == "__main__":
    show_sas()
