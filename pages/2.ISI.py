import streamlit as st
import pandas as pd
from datetime import datetime

def show_isi():
    st.title("失眠严重指数 (ISI)")
    
    with st.form("isi_form"):
        name = st.text_input("姓名")
        
        st.subheader("1. 最近失眠问题严重程度")
        q1a = st.radio("a. 入睡困难", ["无", "轻度", "中度", "重度", "极重度"], horizontal=True)
        q1b = st.radio("b. 睡眠维持困难", ["无", "轻度", "中度", "重度", "极重度"], horizontal=True)
        q1c = st.radio("c. 早醒", ["无", "轻度", "中度", "重度", "极重度"], horizontal=True)
        
        st.subheader("其他问题")
        q2 = st.radio("2. 对睡眠模式满意度", ["很满意", "满意", "一般", "不满意", "很不满意"], horizontal=True)
        q3 = st.radio("3. 失眠对日常功能影响", ["没有干扰", "轻微", "有些", "较多", "很多"], horizontal=True)
        q4 = st.radio("4. 失眠对生活质量影响", ["没有", "轻微", "有些", "较多", "很多"], horizontal=True)
        q5 = st.radio("5. 对睡眠问题的担心程度", ["没有", "轻微", "有些", "较多", "很多"], horizontal=True)
        
        submitted = st.form_submit_button("提交")
        
        if submitted:
            # 计算分数
            score_map = {
                "无": 0, "轻度": 1, "中度": 2, "重度": 3, "极重度": 4,
                "很满意": 0, "满意": 1, "一般": 2, "不满意": 3, "很不满意": 4,
                "没有干扰": 0, "轻微": 1, "有些": 2, "较多": 3, "很多": 4,
                "没有": 0, "轻微": 1, "有些": 2, "较多": 3, "很多": 4
            }
            
            scores = {
                "1a.入睡困难": score_map[q1a],
                "1b.睡眠维持困难": score_map[q1b],
                "1c.早醒": score_map[q1c],
                "2.睡眠满意度": score_map[q2],
                "3.日常功能影响": score_map[q3],
                "4.生活质量影响": score_map[q4],
                "5.担心程度": score_map[q5]
            }
            
            total_score = sum(scores.values())
            
            # 显示结果
            st.subheader("评分结果")
            st.write(f"**总分: {total_score}**")
            st.write("各题目分数:")
            for k, v in scores.items():
                st.write(f"- {k}: {v}")
            
            # 创建数据框
            data = {
                "姓名": [name],
                "1a.入睡困难": [q1a],
                "1b.睡眠维持困难": [q1b],
                "1c.早醒": [q1c],
                "2.睡眠满意度": [q2],
                "3.日常功能影响": [q3],
                "4.生活质量影响": [q4],
                "5.担心程度": [q5],
                "总分": [total_score]
            }
            
            # 添加时间戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            filename = f"{timestamp}_{name}_ISI.csv"
            
            # 创建下载按钮
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="下载结果CSV",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
            
            st.success("问卷提交成功！结果已保存")

if __name__ == "__main__":
    show_isi()
