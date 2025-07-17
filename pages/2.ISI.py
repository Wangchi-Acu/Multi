import streamlit as st, utils

st.set_page_config(page_title="ISI")
st.title("失眠严重指数量表 ISI")

questions = [
    ("入睡困难", ["无","轻度","中度","重度","极重度"]),
    ("睡眠维持困难", ["无","轻度","中度","重度","极重度"]),
    ("早醒", ["无","轻度","中度","重度","极重度"]),
    ("对睡眠模式满意/不满意", ["很满意","满意","一般","不满意","很不满意"]),
    ("失眠对日常功能的影响", ["没有干扰","轻微","有些","较多","很多"]),
    ("在别人眼中的影响程度", ["没有","轻微","有些","较多","很多"]),
    ("对失眠的担心/痛苦程度", ["没有","轻微","有些","较多","很多"])
]

score_map = {"无":0,"轻度":1,"中度":2,"重度":3,"极重度":4,
             "很满意":0,"满意":1,"一般":2,"不满意":3,"很不满意":4,
             "没有干扰":0,"轻微":1,"有些":2,"较多":3,"很多":4}

answers = {}
for txt, opts in questions:
    st.write(f"**{txt}**")
    cols = st.columns(len(opts))
    key = f"isi_{txt}"
    # 初始化
    if key not in st.session_state:
        st.session_state[key] = None
    for idx, opt in enumerate(opts):
        if cols[idx].button(opt, key=f"{key}_{idx}", use_container_width=True):
            st.session_state[key] = opt
    # 高亮当前选中
    if st.session_state[key]:
        st.info(f"已选：{st.session_state[key]}")

if st.button("提交 ISI"):
    if any(st.session_state.get(f"isi_{t}") is None for t, _ in questions):
        st.warning("请完成全部题目")
    else:
        total = sum(score_map[st.session_state[f"isi_{t}"]] for t, _ in questions)
        utils.save_result(st.session_state.get("user_id","匿名"), ISI_total=total)
        st.success(f"ISI 已提交，总分：{total} 分")
