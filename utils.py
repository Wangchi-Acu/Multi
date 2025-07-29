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
# ---------- 美化导航提示 ----------
if __name__ == "__main__":
    st.set_page_config(
        page_title="失眠专病门诊量表测评系统",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # 渐变背景容器
    st.markdown(
        """
        <style>
            .main-wrapper {
                background: linear-gradient(135deg,#e3f2fd 0%,#bbdefb 100%);
                padding: 3rem 1rem;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .big-title {
                font-size: 2.4rem;
                font-weight: 700;
                color: #0d47a1;
                margin-bottom: 0.5rem;
            }
            .sub-title {
                font-size: 2rem;
                font-weight: 600;
                color: #1565c0;
                margin-bottom: 1.5rem;
            }
            .guide {
                font-size: 1.3rem;
                color: #1a237e;
            }
            .arrow {
                font-size: 1.8rem;
                animation: bounce 1.5s infinite;
            }
            @keyframes bounce {
                0%,100% { transform: translateY(0);}
                50% { transform: translateY(-6px);}
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown(
            """
            <div class="main-wrapper">
                <div class="big-title">失眠专病门诊量表</div>
                <div class="sub-title">测评系统</div>
                <div class="guide">
                    <span class="arrow">👆👆👆</span><br/>
                    点击左上角 <b>>> 开始测评</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
