import time

import streamlit as st

from agent.agent_react import AgentReact
from utils.history_tool import load_user_history, save_user_history

# 启动命令：streamlit run app.py

st.title("岗位搜索智能助手")
# 分隔符
st.divider()

# 生成或获取用户 ID（支持自定义用户名）
if "user_id" not in st.session_state:
    # 可以通过 URL 参数 ?user=test 或者在侧边栏输入自定义用户名
    url_params = st.query_params
    custom_user = url_params.get("user", "")

    if custom_user:
        st.session_state["user_id"] = custom_user
    else:
        st.session_state["user_id"] = "default"

        st.info(f"当前用户：{st.session_state['user_id']}")

# 初始化 Agent（带用户 ID）
if "agent" not in st.session_state:
    st.session_state["agent"] = AgentReact(user_id=st.session_state["user_id"])
# 获取历史消息显示
if "message" not in st.session_state:
    # 从文件加载历史对话
    loaded_history = load_user_history(st.session_state["user_id"], limit=20)

    if loaded_history:
        st.session_state["message"] = loaded_history
    else:
        st.session_state["message"] = [
            {
                "role": "ai",
                "content": "你好，欢迎使用岗位搜索智能助手。",
            }
        ]

# 显示历史消息
for message in st.session_state["message"]:
    # 跳过 timestamp 字段（不显示）
    content = message.get("content", "")
    role = message.get("role", "ai")
    if content:
        st.chat_message(role).write(content)

prompt = st.chat_input()

if prompt:
    st.chat_message("human").write(prompt)
    st.session_state["message"].append(
        {
            "role": "human",
            "content": prompt,
        }
    )
    save_user_history(st.session_state["user_id"], "human", prompt)
    stream_list = []
    with st.spinner("思考中..."):
        agent = st.session_state["agent"]

        # 获取历史对话（用于上下文）
        history = load_user_history(st.session_state["user_id"], limit=10)
        # 设置流式输出回复
        res = agent.execute_stream(prompt, history=history)

        def capture(chunks, cache):
            for chunk in chunks:
                cache.append(chunk)
                # 设置单字流式输出的延迟
                for char in chunk:
                    time.sleep(0.01)
                    yield char


        st.chat_message("ai").write_stream(capture(chunks=res, cache=stream_list))
        ai_response = "".join(stream_list)

        # 保存 AI 回复到历史
        save_user_history(st.session_state["user_id"], "ai", ai_response)

        st.session_state["message"].append(
            {
                "role": "ai",
                "content": "".join(stream_list),
            }
        )
        st.rerun()
