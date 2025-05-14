import streamlit as st
from agent.agent import react_agent_graph
from agent.agent_chains import graph
from utils.schema_utils import extract_schema
from utils.prompt import prompt, build_prompt
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


# Streamlit UI
st.title("🧠 NL2SQL 查询助手")
st.markdown("输入自然语言问题，自动生成 SQL 并查询数据库。")

user_input = st.text_input("请输入您的问题，例如：'每个产品的总销量是多少？'")

if "sql_generated" not in st.session_state:
    st.session_state.sql_generated = False
if st.button("生成 SQL"):
    with st.spinner("正在生成 SQL..."):
        # img_bytes = graph.get_graph().draw_mermaid_png()
        config = {"configurable": {"thread_id": "1"}}
        # st.image(img_bytes)
        for step in graph.stream({"question": user_input}, config=config, stream_mode="updates"):
            print(step)
            st.text(step)
        st.session_state.sql_generated = True
if st.session_state.sql_generated:
    user_decision = st.text_input("是否执行 SQL？请输入 '是' 或 '否'")
    if user_decision.strip() == "是":
        try:
            with st.spinner("正在执行 SQL..."):
                config = {"configurable": {"thread_id": "1"}}
                for step in graph.stream(None, config=config, stream_mode="updates"):
                    print(step)
                    st.text(step)
        except Exception as e:
            st.error(f"SQL 执行失败: {str(e)}")
    elif user_decision.strip() == "否":
        st.success("SQL 执行取消")


