import streamlit as st, utils

st.set_page_config(page_title="FSS 疲劳量表")
st.title("疲劳严重程度量表 FSS")

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

with st.form("fss"):
    opts = list(range(8))  # 0-7
    answers = [st.select_slider(q, opts, format_func=lambda x: f"{x} 分") for q in questions]
    submitted = st.form_submit_button("提交 FSS")
if submitted:
    total = sum(answers)
    utils.save_result(st.session_state.get("user_id","匿名"), FSS_total=total)
    level = "正常" if total < 36 else "需进一步评估"
    st.success(f"FSS 已提交，总分：{total} 分，{level}")
