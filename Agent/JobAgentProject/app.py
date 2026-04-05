import time
import streamlit as st

from agent.agent_react import AgentReact
from utils.history_tool import (
    clear_user_history,
    load_user_history,
    save_user_history,
)

# 启动命令：streamlit run app.py

# 页面基础配置
st.set_page_config(
    page_title="岗位搜索智能助手",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题和描述
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔍 岗位搜索智能助手")
with col2:
    st.caption(f"👤 用户：{st.session_state.get('user_id', 'default')}")

st.markdown("智能匹配您的理想岗位，支持多条件搜索和推荐")
st.divider()

# ==================== 侧边栏配置 ====================
with st.sidebar:
    # 用户管理
    st.subheader("👤 用户管理")
    custom_user = st.text_input(
        "用户名",
        value=st.session_state.get("user_id", "default"),
        help="输入自定义用户名切换用户"
    )
    
    if custom_user and custom_user != st.session_state.get("user_id"):
        st.session_state["user_id"] = custom_user
        st.session_state["agent"] = AgentReact(user_id=custom_user)
        st.rerun()
    
    # 显示当前用户
    st.info(f"当前用户：**{st.session_state['user_id']}**")
    
    st.divider()
    
    # 历史对话管理
    st.subheader("📜 历史管理")
    
    if st.button("🗑️ 清空对话历史", use_container_width=True):
        user_id = st.session_state["user_id"]
        clear_user_history(user_id)
        st.success("✅ 历史已清空！")
        st.session_state["message"] = [
            {"role": "ai", "content": "你好，欢迎使用岗位搜索智能助手。"}
        ]
        time.sleep(1)
        st.rerun()
    
    if st.button("🔄 重新加载历史", use_container_width=True):
        loaded_history = load_user_history(st.session_state["user_id"], limit=20)
        if loaded_history:
            st.session_state["message"] = loaded_history
            st.success("✅ 历史已重新加载！")
            time.sleep(1)
            st.rerun()
    
    st.divider()
    
    # 统计信息
    st.subheader("📊 统计信息")
    history_count = len(load_user_history(st.session_state["user_id"], limit=99))
    st.metric("对话条数", history_count)

# ==================== 初始化 Agent ====================
if "agent" not in st.session_state:
    st.session_state["agent"] = AgentReact(user_id=st.session_state["user_id"])

# 初始化消息历史
if "message" not in st.session_state:
    loaded_history = load_user_history(st.session_state["user_id"], limit=20)
    
    if loaded_history:
        st.session_state["message"] = loaded_history
    else:
        st.session_state["message"] = [
            {
                "role": "ai",
                "content": "👋 你好，欢迎使用岗位搜索智能助手！我可以帮你搜索岗位信息、分析岗位需求等。请告诉我你的需求吧～",
            }
        ]

# ==================== 显示欢迎卡片（如果是第一条消息） ====================
if len(st.session_state["message"]) <= 1:
    st.info("✨ **欢迎使用岗位搜索智能助手**\n\n"
            "**我可以帮助你：**\n"
            "- 🔍 搜索特定地区、职位的岗位信息\n"
            "- 📊 分析岗位需求和薪资水平\n"
            "在下方输入框告诉我你的需求吧！")

# ==================== 显示历史消息 ====================
for idx, message in enumerate(st.session_state["message"]):
    content = message.get("content", "")
    role = message.get("role", "ai")
    
    if content:
        with st.chat_message(role):
            st.write(content)

# ==================== 用户输入处理 ====================
prompt = st.chat_input("请输入你的需求，例如：我想找北京的 Python 工程师岗位...")

if prompt:
    # 显示用户消息
    st.chat_message("human").write(prompt)
    st.session_state["message"].append(
        {
            "role": "human",
            "content": prompt,
        }
    )
    save_user_history(st.session_state["user_id"], "human", prompt)
    
    stream_list = []
    
    # 使用容器包装思考状态
    with st.container():
        with st.spinner("🤔 正在搜索中，请稍候..."):
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
            
            # 显示 AI 回复
            with st.chat_message("ai"):
                response = st.write_stream(capture(chunks=res, cache=stream_list))
                ai_response = response
            
            # 保存 AI 回复到历史
            save_user_history(st.session_state["user_id"], "ai", ai_response)
            
            st.session_state["message"].append(
                {
                    "role": "ai",
                    "content": ai_response,
                }
            )
    
    # 自动滚动到底部
    st.rerun()
