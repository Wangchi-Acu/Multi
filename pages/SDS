import streamlit as st, utils

st.set_page_config(page_title="SDS 抑郁量表")
st.title("抑郁自评量表 SDS")

questions = [
    "我觉得闷闷不乐，情绪低沉",
    "我觉得一天之中早晨最好（反向）",
    "我一阵阵哭出来或觉得想哭",
    "我晚上睡眠不好",
    "我吃得跟平常一样多（反向）",
    "我与异性密切接触时和以往一样感到愉快（反向）",
    "我发觉我的体重在下降",
    "我有便秘的苦恼",
    "我心跳比平时快",
    "我无缘无故地感到疲乏",
    "我的头脑跟平常一样清楚（反向）",
    "我觉得经常做的事情并没有困难（反向）",
    "我觉得不安而平静不下来",
    "我对将来抱有希望（反向）",
    "我比平常容易生气激动",
    "我觉得作出决定是容易的（反向）",
    "我觉得自己是个有用的人，有人需要我（反向）",
    "我的生活过得很有意思（反向）",
    "我认为如果我死了别人会生活得好些",
    "平常感兴趣的事我仍然照样感兴趣（反向）"
]

with st.form("sds"):
    opts = ["从无或偶尔","有时","经常","总是如此"]
    answers = [st.select_slider(q, opts, key=f"sds_{i}") for i,q in enumerate(questions)]
    submitted = st.form_submit_button("提交 SDS")
if submitted:
    score_map = {"从无或偶尔":1,"有时":2,"经常":3,"总是如此":4}
    raw = 0
    reverse_idx = [1,4,5,10,11,13,16,17,19]  # 反向题
    for i, v in enumerate(answers):
        s = score_map[v]
        raw += (5-s) if i in reverse_idx else s
    std = int(raw * 1.25 + 0.5)
    utils.save_result(st.session_state.get("user_id","匿名"), SDS_raw=raw, SDS_std=std)
    st.success(f"SDS 已提交，标准分：{std} 分")
