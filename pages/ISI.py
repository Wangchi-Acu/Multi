import streamlit as st, utils
st.set_page_config(page_title="ISI")
st.title("失眠严重指数量表 ISI")

with st.form("isi"):
    q1 = st.selectbox("入睡困难", ["无","轻度","中度","重度","极重度"])
    q2 = st.selectbox("睡眠维持困难", ["无","轻度","中度","重度","极重度"])
    q3 = st.selectbox("早醒", ["无","轻度","中度","重度","极重度"])
    q4 = st.selectbox("对睡眠模式满意/不满意", ["很满意","满意","一般","不满意","很不满意"])
    q5 = st.selectbox("失眠对日常功能的影响", ["没有干扰","轻微","有些","较多","很多"])
    q6 = st.selectbox("在别人眼中的影响程度", ["没有","轻微","有些","较多","很多"])
    q7 = st.selectbox("对失眠的担心/痛苦程度", ["没有","轻微","有些","较多","很多"])
    submitted = st.form_submit_button("提交 ISI")
if submitted:
    score_map = {"无":0,"轻度":1,"中度":2,"重度":3,"极重度":4,
                 "很满意":0,"满意":1,"一般":2,"不满意":3,"很不满意":4,
                 "没有干扰":0,"轻微":1,"有些":2,"较多":3,"很多":4}
    total = sum(score_map[v] for v in [q1,q2,q3,q4,q5,q6,q7])
    utils.save_result(st.session_state.get("user_id","匿名"), ISI_total=total)
    st.success(f"ISI 已提交，总分：{total} 分")
