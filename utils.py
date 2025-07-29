#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os, csv, datetime

# ---------- 通用保存 ----------
def save_result(user_id, **scores):
    """
    user_id : 时间戳_姓名
    scores  : 各量表返回的字典
    """
    base_dir = r"F:\10量表结果"
    today = datetime.datetime.now().strftime("%Y%m%d")
    folder = os.path.join(base_dir, today + "_" + user_id)
    os.makedirs(folder, exist_ok=True)

    # 量表名 = scores 中 key 的前缀
    scale = list(scores.keys())[0].split("_")[0]
    csv_path = os.path.join(folder, f"{scale}.csv")

    # 写表头或追加
    write_header = not os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=scores.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(scores)

import streamlit as st

# 当 utils.py 被 Streamlit 当作入口文件时，显示导航提示
if __name__ == "__main__":
    st.set_page_config(page_title="失眠多量表测评", layout="centered")
    st.markdown(
        """
        <h2 style='text-align:center;'>失眠专病门诊量表测评系统</h2>
        <h2 style='text-align:center;'>测评系统</h2>
        <p style='text-align:center;font-size:1.2rem;'>
           👆👆👆 点击左上角 <b>“>>”</b> 展开侧边栏
           开始测评吧！
        </p>
        """,
        unsafe_allow_html=True
    )
