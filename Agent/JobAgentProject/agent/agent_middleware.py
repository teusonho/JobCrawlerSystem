from typing import Callable

from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command

from utils.logger_tool import logger


def extract_message_content(content):
    """提取消息内容，处理 content 可能是字符串或列表的情况"""
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        return "".join(text_parts).strip()
    else:
        return str(content).strip()


@wrap_tool_call
def tool_monitor(
        request: ToolCallRequest,    # 封装的请求数据
        handler: Callable[[ToolCallRequest], ToolMessage | Command],    # 执行的函数
)-> ToolMessage | Command:
    logger.info(f"[tool_monitor]调用工具：{request.tool_call['name']}")
    logger.info(f"[tool_monitor]调用参数：{request.tool_call['args']}")
    try:
        res = handler(request)
        logger.info(f"[tool_monitor]工具返回结果：{res}")
        # 调用文本生成上下文时，设置标志位
        if request.tool_call["name"] == "fill_context_for_report":
            request.runtime.context["report"] = True
        return res
    except Exception as e:
        logger.error(f"[tool_monitor]工具调用失败：{request.tool_call['name']}\nERROR:{e}")
        raise e

@before_model
def log_before_model(
        state: AgentState,      # 整个 Agent 智能体的状态记录
        runtime: Runtime,       # 执行过程中的上下文
):
    logger.info(f"[log_before_model]消息数：{len(state['messages'])}")
    
    # 安全提取消息内容
    latest_msg = state['messages'][-1]
    content_str = extract_message_content(latest_msg.content)
    
    logger.debug(f"[log_before_model]消息：{type(latest_msg).__name__}\n{content_str}")
    return None
