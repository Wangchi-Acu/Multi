import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

# --------------- 通用保存函数 ---------------
def save_csv_isi(name, rows_dict):
    """
    保存 ISI 结果到 F:\10量表结果\年月日_姓名_ISI.csv
    rows_dict 必须包含 '姓名' '时间戳' 及各题原始选项、分值、总分
    """
    save_dir = r"F:\10量表结果"
    os.makedirs(save_dir, exist_ok=True)
    # 文件名：年月日时分+姓名+量表名称.csv
    file_name = f"{rows_dict['时间戳']}_{name}_ISI.csv"
    path = os.path.join(save_dir, file_name)

    # 写表头或追加
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows_dict.keys())
        writer.writeheader()
        writer.writerow(rows_dict)
    return path


# --------------- 主界面 ---------------
def show_isi():
    st.set_page_config(page_title="ISI 失眠量表")
    st.title("失眠严重指数量表 ISI")

    with st.form("isi_form"):
        name = st.text_input("姓名")

        # 统一映射
        score_map = {
            "无": 0, "轻度": 1, "中度": 2, "重度": 3, "极重度": 4,
            "很满意": 0, "满意": 1, "一般": 2, "不满意": 3, "很不满意": 4,
            "没有干扰": 0, "轻微": 1, "有些": 2, "较多": 3, "很多": 4,
            "没有": 0, "轻微": 1, "有些": 2, "较多": 3, "很多": 4
        }

        # 题目列表（文本选项）
        questions = [
            ("1a. 入睡困难", ["无", "轻度", "中度", "重度", "极重度"]),
            ("1b. 睡眠维持困难", ["无", "轻度", "中度", "重度", "极重度"]),
            ("1c. 早醒", ["无", "轻度", "中度", "重度", "极重度"]),
            ("2. 睡眠满意度", ["很满意", "满意", "一般", "不满意", "很不满意"]),
            ("3. 日常功能影响", ["没有干扰", "轻微", "有些", "较多", "很多"]),
            ("4. 生活质量影响", ["没有", "轻微", "有些", "较多", "很多"]),
            ("5. 担心程度", ["没有", "轻微", "有些", "较多", "很多"])
        ]

        # 存储每题选择
        choices = {}
        for txt, opts in questions:
            choices[txt] = st.radio(txt, opts, horizontal=True)

        submitted = st.form_submit_button("提交")

        if submitted:
            if not name:
                st.warning("请输入姓名")
                st.stop()

            # 计算分值 & 构建记录
            record = {"姓名": name, "时间戳": datetime.now().strftime("%Y%m%d%H%M")}
            total = 0
            for txt, opts in questions:
                opt = choices[txt]
                val = score_map[opt]
                record[f"{txt}(选项)"] = opt
                record[f"{txt}(分值)"] = val
                total += val
            record["总分"] = total

            # 保存本地 CSV
            path = save_csv_isi(name, record)

            # 展示结果
            st.subheader("评分结果")
            st.write(f"**总分：{total}**")
            for k, v in choices.items():
                st.write(f"- {k}：{v}（{score_map[v]} 分）")

            # 下载按钮
            with open(path, "rb") as f:
                st.download_button(
                    label="📥 下载结果 CSV",
                    data=f,
                    file_name=os.path.basename(path),
                    mime="text/csv"
                )
            st.success("问卷提交成功！")

if __name__ == "__main__":
    show_isi()
