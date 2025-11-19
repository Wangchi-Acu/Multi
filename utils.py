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

# 当 utils.py 被当作入口文件时，显示导航提示
# ---------- 美化导航提示 ----------

if __name__ == "__main__":
    # ========== 首页四色卡片布局 ==========
    st.set_page_config(page_title="针灸科失眠专病门诊量表测评系统",
                       layout="centered",
                       initial_sidebar_state="collapsed")

    # 全局样式：卡片容器
    st.markdown("""
    <style>
    .card {
        border-radius: 12px;
        padding: 1.2rem 0.8rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        text-align: center;
    }
    .card-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .card-sleep   { background: linear-gradient(135deg,#e3f2fd 0%,#bbdefb 100%); color: #0d47a1; }
    .card-report  { background: linear-gradient(135deg,#fff3e0 0%,#ffe0b2 100%); color: #e65100; }
    .card-scale   { background: linear-gradient(135deg,#f3e5f5 0%,#e1bee7 100%); color: #4a148c; }
    .card-doctor  { background: linear-gradient(135deg,#e8f5e9 0%,#c8e6c9 100%); color: #1b5e20; }
    .stButton>button {
        border-radius: 8px;
        height: 2.6rem;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    # 顶部 Logo + 标题
    _, cen, _ = st.columns([1, 2, 1])
    with cen:
        st.image("jsszyylogo.png", use_column_width=True)
    st.markdown('<div style="text-align:center;font-size:2.2rem;font-weight:700;color:#0d47a1;margin-bottom:0.3rem;">'
                '针灸科失眠专病门诊<br>量表测评系统</div>',
                unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # ① 睡眠日记区域
    # ------------------------------------------------------------------
    st.markdown('<div class="card card-sleep">'
                '<div class="card-title">🛏️ 睡眠日记</div>'
                '<div style="margin-bottom:0.8rem;">每日睡前填写，记录睡眠情况</div>',
                unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("立即填写睡眠日记", type="primary", use_container_width=True):
            st.switch_page("pages/睡眠日记.py")
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # ② 门诊监测报告下载区域
    # ------------------------------------------------------------------
    st.markdown('<div class="card card-report">'
                '<div class="card-title">📄 门诊监测报告下载</div>'
                '<div style="margin-bottom:0.8rem;">输入姓名即可下载脑电分析报告</div>',
                unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("下载报告", type="primary", use_container_width=True):
            st.switch_page("pages/下载门诊监测报告.py")
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # ③ 量表评估区域
    # ------------------------------------------------------------------
    st.markdown('<div class="card card-scale">'
                '<div class="card-title">📋 量表评估</div>'
                '<div style="margin-bottom:0.8rem;">完成各量表自评，协助医生评估</div>',
                unsafe_allow_html=True)
    scale_buttons = [
        ("🛋️ PSQI 睡眠质量", "pages/量表① PSQI.py"),
        ("😴 ISI 失眠严重程度", "pages/量表② ISI.py"),
        ("🌀 HAS 嗜睡量表", "pages/量表③ HAS.py"),
        ("⚡ FSS 疲劳量表", "pages/量表④ FSS.py"),
        ("😰 SAS 焦虑自评", "pages/量表⑤ SAS.py"),
        ("😞 SDS 抑郁自评", "pages/量表⑥ SDS.py"),
    ]
    cols = st.columns(3)  # 每行 3 个按钮
    for i, (txt, page) in enumerate(scale_buttons):
        with cols[i % 3]:
            if st.button(txt, use_container_width=True):
                st.switch_page(page)
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # ④ 医生专用查询区域
    # ------------------------------------------------------------------
    st.markdown('<div class="card card-doctor">'
                '<div class="card-title">👨‍⚕️ 医生专用查询</div>'
                '<div style="margin-bottom:0.8rem;">查看患者睡眠日记与量表汇总</div>',
                unsafe_allow_html=True)
    doctor_buttons = [
        ("📊 睡眠日记查询", "pages/睡眠日记查询.py"),
        ("📈 量表汇总查询", "pages/量表汇总查询.py"),
    ]
    cols = st.columns(2)  # 每行 2 个按钮
    for i, (txt, page) in enumerate(doctor_buttons):
        with cols[i % 2]:
            if st.button(txt, use_container_width=True):
                st.switch_page(page)
    st.markdown('</div>', unsafe_allow_html=True)
