import streamlit as st, utils

st.set_page_config(page_title="HAS 过度觉醒量表")
st.title("过度觉醒量表 HAS")

questions = [
    "我很有条理（反向）",
    "我早晨不容易醒来（反向）",
    "我工作非常细心（反向）",
    "我总是控制不住的胡思乱想",
    "对于自己的感情和感受，我总会在意很多",
    "明亮的灯光、拥挤的人群、嘈杂的噪音或拥挤的交通让我心烦意乱",
    "我在晚上状态最好",
    "我无法午睡，怎么想办法也睡不着",
    "我往往会预想有可能发生的麻烦",
    "我的卧室一团乱",
    "我总觉得处处被针对",
    "当很多事情一起发生的时候我会很紧张",
    "我善于处理细枝末节（反向）",
    "我入睡困难",
    "我处事小心谨慎（反向）",
    "晚上躺在床上时，我也一直在想各种各样的事",
    "突然的、巨大的噪音会让我久久不能平静",
    "我认真的有些过分（反向）",
    "咖啡因（茶叶）会对我产生严重的不良作用",
    "当事情不顺时，我往往会感到沮丧",
    "我的生活千篇一律，没有新意",
    "我的脑海里总是重复某些想法",
    "我要花很长时间才能下决心",
    "酒精让我昏昏欲睡",
    "我很容易流泪",
    "某些事情发生后很久之后，我还念念不忘"
]

with st.form("has"):
    opts = ["从来不","偶尔有","经常有","绝大部分时间有"]
    answers = [st.select_slider(q, opts, key=f"has_{i}") for q in questions]
    submitted = st.form_submit_button("提交 HAS")
if submitted:
    score_map = {"从来不":0,"偶尔有":1,"经常有":2,"绝大部分时间有":3}
    total = sum(score_map[v] for v in answers)
    level = "正常" if total <= 32 else "过度觉醒"
    utils.save_result(st.session_state.get("user_id","匿名"), HAS_total=total, HAS_level=level)
    st.success(f"HAS 已提交，总分：{total} 分，{level}")
