import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv

# ---------- Streamlit 界面 ----------
st.set_page_config(page_title="抑郁自评量表 (SDS)", layout="centered")
st.title("江苏省中医院针灸科失眠专病门诊")
st.markdown(
    "<h3 style='color:#555555;'>抑郁自评量表 (SDS)在线问卷</h3>",
    unsafe_allow_html=True
)

def save_csv_sds(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['时间戳']}_{name}_SDS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def show_sds():
    name = st.text_input("姓名")

    questions = [
        "我觉得闷闷不乐，情绪低沉",
        "我觉得一天之中早晨最好",
        "我一阵阵哭出来或觉得想哭",
        "我晚上睡眠不好",
        "我吃得跟平常一样多",
        "我与异性密切接触时和以往一样感到愉快",
        "我发觉我的体重在下降",
        "我有便秘的苦恼",
        "我心跳比平时快",
        "我无缘无故地感到疲乏",
        "我的头脑跟平常一样清楚",
        "我觉得经常做的事情并没有困难",
        "我觉得不安而平静不下来",
        "我对将来抱有希望",
        "我比平常容易生气激动",
        "我觉得作出决定是容易的",
        "我觉得自己是个有用的人，有人需要我",
        "我的生活过得很有意思",
        "我认为如果我死了别人会生活得好些",
        "平常感兴趣的事我仍然照样感兴趣"
    ]

    opts = ["从无或偶尔","有时","经常","总是如此"]
    score_map = {"从无或偶尔":1,"有时":2,"经常":3,"总是如此":4}
    reverse_idx = {1,4,5,10,11,13,15,16,17,19}  # 0 开始

    choices = {}
    for i, q in enumerate(questions, 1):
        st.write(f"{i}. {q}")
        choices[q] = st.radio(label="", options=opts, horizontal=True, key=f"sds_{i}")

    if st.button("提交 SDS"):
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

        path = save_csv_sds(name, record)

        st.subheader("评分结果")
        st.write(f"**原始分：{raw}  |  标准分：{std}**")
        level = "无抑郁" if std < 53 else "轻度抑郁" if std < 63 else "中度抑郁" if std < 73 else "重度抑郁"
        st.info(f"结论：{level}")

        with open(path, "rb") as f:
            st.download_button(
                label="📥 下载结果 CSV",
                data=f,
                file_name=os.path.basename(path),
                mime="text/csv"
            )
        st.success("SDS 提交成功！")

if __name__ == "__main__":
    show_sds()
