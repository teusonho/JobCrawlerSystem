import os
from typing import List, Optional

from utils.config_tool import agent_conf
from utils.logger_tool import logger
from utils.path_tool import get_abs_path

try:
    from langchain_community.chat_message_histories import FileChatMessageHistory
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
except Exception as e:  # pragma: no cover
    FileChatMessageHistory = None  # type: ignore[assignment]
    AIMessage = BaseMessage = HumanMessage = SystemMessage = object  # type: ignore[misc,assignment]
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


USER_HISTORY_PATH = get_abs_path(agent_conf["user_history_path"])


def ensure_user_history_dir(user_id: str) -> str:
    """确保用户历史目录存在"""
    user_dir = os.path.join(USER_HISTORY_PATH, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def _ensure_langchain_available() -> None:
    if FileChatMessageHistory is None:
        raise RuntimeError(
            "未检测到 LangChain 相关依赖，无法使用对话历史存储。"
            f" 原始导入错误：{_IMPORT_ERROR}"
        )


def _get_history_file(user_id: str) -> str:
    user_dir = ensure_user_history_dir(user_id)
    # LangChain 的 FileChatMessageHistory 会把消息持久化到该文件
    return os.path.join(user_dir, "history_langchain.json")


def get_chat_message_history(user_id: str) -> "FileChatMessageHistory":
    """获取（并持久化到文件的）LangChain 对话历史对象"""
    _ensure_langchain_available()
    return FileChatMessageHistory(_get_history_file(user_id))


def _to_role(msg: "BaseMessage") -> str:
    # 兼容 LangChain message 类型
    if isinstance(msg, HumanMessage):
        return "human"
    elif isinstance(msg, AIMessage):
        return "ai"
    elif isinstance(msg, SystemMessage):
        return "system"
    # 兜底：尽量和现有 UI/agent 角色保持一致
    return getattr(msg, "type", "ai") or "ai"


def load_user_history(user_id: str, limit: int = 10) -> List[dict]:
    """
    加载用户历史对话（基于 LangChain 的持久化历史）。
    """
    try:
        history = get_chat_message_history(user_id)
        messages: List["BaseMessage"] = history.messages or []
        # 只加载最近10条
        tail = messages[-limit:] if limit and len(messages) > limit else messages
        return [{"role": _to_role(m), "content": getattr(m, "content", "") or ""} for m in tail]
    except Exception as e:
        logger.error(f"[load_user_history]加载历史失败：{e}")
        return []


def save_user_history(user_id: str, role: str, content: str) -> None:
    """
    保存对话到历史（基于 LangChain 的持久化历史）。

    :param role: 兼容现有调用方：'human' 或 'ai'（也兼容 'user'/'assistant'）
    """
    try:
        history = get_chat_message_history(user_id)
        normalized = (role or "").lower().strip()
        if normalized in {"human", "user"}:
            history.add_user_message(content or "")
        elif normalized in {"ai", "assistant"}:
            history.add_ai_message(content or "")
        elif normalized == "system":
            # FileChatMessageHistory 支持直接追加 BaseMessage
            history.add_message(SystemMessage(content=content or ""))
        else:
            # 未知角色统一按 human 处理，避免丢上下文
            history.add_user_message(content or "")
        logger.info(f"[save_user_history]保存用户 {user_id} 的历史对话(role={normalized})")
    except Exception as e:
        logger.error(f"[save_user_history]保存历史失败：{e}")


def clear_user_history(user_id: str) -> None:
    """清空指定用户的历史（LangChain 持久化文件）"""
    try:
        history = get_chat_message_history(user_id)
        history.clear()
        logger.info(f"[clear_user_history]清空用户 {user_id} 的历史对话")
    except Exception as e:
        logger.error(f"[clear_user_history]清空历史失败：{e}")


def get_history_file_path(user_id: str) -> str:
    """对外暴露当前使用的历史文件路径（便于运维/排查）"""
    return _get_history_file(user_id)