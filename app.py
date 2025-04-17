import streamlit as st
from agent.agent import react_agent_graph
from utils.schema_utils import extract_schema
from utils.prompt import prompt, build_prompt
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage,ToolMessage


# Streamlit UI
st.title("🧠 NL2SQL 查询助手")
st.markdown("输入自然语言问题，自动生成 SQL 并查询数据库。")

user_input = st.text_input("请输入您的问题，例如：'每个产品的总销量是多少？'")
# print(prompt_val.messages.pretty_print())

if st.button("生成 SQL"):
    with st.spinner("正在生成 SQL..."):
        initial_state = {"input": user_input, "top_k": 5, "dialect": "PostgreSQL", "messages": []}
        i = 0
        for step in react_agent_graph.stream(initial_state, stream_mode=["values"]):
            message = step[1]["messages"]
            if len(message) > 0:
                message = message[-1]
            print(f'-------------step: {i}')
            # print(message)
            i += 1
            if isinstance(message, AIMessage):
                # 处理动作（如调用工具）
                for action in message.tool_calls:
                    st.text(f"执行动作: {action.get('name')}，输入: {action.get('args')}")
                if message.response_metadata.get("finish_reason") == "stop":
                    st.success("查询成功，结果如下：")
                    st.text(message.content)
            elif isinstance(message, ToolMessage):
                # 处理观察结果
                st.text(f"观察结果: {message.content}")
            st.text(message)


