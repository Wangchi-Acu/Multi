import streamlit as st
import pandas as pd
from datetime import datetime
import os, csv

# ---------- Streamlit 界面 ----------
st.set_page_config(page_title="过度觉醒量表 （HAS）", layout="centered")
st.image("jsszyylogo.png", width=500)  # 更改url_to_your_logo.png为你的logo图片链接，调整width为适当的大小
st.title("江苏省中医院针灸科失眠专病门诊")
st.markdown(
    "<h3 style='color:#555555;'>过度觉醒量表 （HAS）在线问卷</h3>",
    unsafe_allow_html=True
)

def save_csv_has(name, record):
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{record['时间戳']}_{name}_HAS.csv"
    path = os.path.join(save_dir, file_name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    return path

def show_has():
    
    name = st.text_input("姓名")

    questions = [
        "我很有条理",
        "我早晨不容易醒来",
        "我工作非常细心",
        "我总是控制不住的胡思乱想",
        "对于自己的感情和感受，我总会在意很多",
        "明亮的灯光、拥挤的人群、嘈杂的噪音或拥挤的交通让我心烦意乱",
        "我在晚上状态最好",
        "我无法午睡，怎么想办法也睡不着",
        "我往往会预想有可能发生的麻烦",
        "我的卧室一团乱",
        "我总觉得处处被针对",
        "当很多事情一起发生的时候我会很紧张",
        "我善于处理细枝末节",
        "我入睡困难",
        "我处事小心谨慎",
        "晚上躺在床上时，我也一直在想各种各样的事",
        "突然的、巨大的噪音会让我久久不能平静",
        "我认真的有些过分",
        "咖啡因（茶叶）会对我产生严重的不良作用",
        "当事情不顺时，我往往会感到沮丧",
        "我的生活千篇一律，没有新意",
        "我的脑海里总是重复某些想法",
        "我要花很长时间才能下决心",
        "酒精让我昏昏欲睡",
        "我很容易流泪",
        "某些事情发生后很久之后，我还念念不忘"
    ]

    opts = ["从来不","偶尔有","经常有","绝大部分时间有"]
    score_map = {"从来不":0,"偶尔有":1,"经常有":2,"绝大部分时间有":3}

    choices = {}
    for i, q in enumerate(questions, 1):
        st.write(f"{i}. {q}")
        choices[q] = st.radio(label="", options=opts, horizontal=True, key=f"has_{i}")

    if st.button("提交 HAS"):
        if not name:
            st.warning("请输入姓名")
            st.stop()

        record = {"姓名": name, "时间戳": datetime.now().strftime("%Y%m%d%H%M")}
        total = 0
        for q, opt in choices.items():
            val = score_map[opt]
            record[f"{q}(选项)"] = opt
            record[f"{q}(分值)"] = val
            total += val
        record["总分"] = total

        path = save_csv_has(name, record)

        st.subheader("评分结果")
        st.write(f"**总分：{total}**")
        level = "正常" if total <= 32 else "过度觉醒"
        st.info(f"结论：{level}")

        with open(path, "rb") as f:
            st.download_button(
                label="📥 下载结果 CSV",
                data=f,
                file_name=os.path.basename(path),
                mime="text/csv"
            )
        st.success("HAS 提交成功！")

if __name__ == "__main__":
    show_has()
