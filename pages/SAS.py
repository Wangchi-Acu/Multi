import streamlit as st, utils

st.set_page_config(page_title="SAS 焦虑量表")
st.title("焦虑自评量表 SAS")

questions = [
    "我觉得比平常容易紧张和着急",
    "我无缘无故地感到害怕",
    "我容易心里烦乱或觉得惊恐",
    "我觉得我可能将要发疯",
    "*我觉得一切都很好，也不会发生什么不幸（反向）",
    "我手脚发抖打颤",
    "我因为头痛、颈痛和背痛而苦恼",
    "我感觉容易衰弱和疲乏",
    "*我觉得心平气和，并且容易安静地坐着（反向）",
    "我觉得心跳得很快",
    "我因为一阵阵头晕而苦恼",
    "我有晕倒发作或觉得要晕倒似的",
    "*我吸气呼气都感到很容易（反向）",
    "我的手脚麻木和刺痛",
    "我因为胃痛和消化不良而苦恼",
    "我常常要小便",
    "*我的手常常是干燥温暖的（反向）",
    "我脸红发热",
    "*我容易入睡并且一夜睡得很好（反向）",
    "我做噩梦"
]

with st.form("sas"):
    opts = ["从无或偶尔","有时","经常","总是如此"]
    answers = [st.select_slider(q, opts, key=f"sas_{i}") for i,q in enumerate(questions)]
    submitted = st.form_submit_button("提交 SAS")
if submitted:
    score_map = {"从无或偶尔":1,"有时":2,"经常":3,"总是如此":4}
    raw = 0
    reverse_idx = [4,8,12,16,18]  # 题目序号（从 0 开始）
    for i, v in enumerate(answers):
        s = score_map[v]
        raw += (5-s) if i in reverse_idx else s
    std = int(raw * 1.25 + 0.5)
    utils.save_result(st.session_state.get("user_id","匿名"), SAS_raw=raw, SAS_std=std)
    st.success(f"SAS 已提交，标准分：{std} 分")
