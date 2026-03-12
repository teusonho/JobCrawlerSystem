import json
import os
from datetime import datetime

from utils.config_tool import agent_conf
from utils.path_tool import get_abs_path
from utils.logger_tool import logger

# 获取用户历史路径
USER_HISTORY_PATH = get_abs_path(agent_conf["user_history_path"])


def ensure_user_history_dir(user_id: str) -> str:
    """确保用户历史目录存在"""
    user_dir = os.path.join(USER_HISTORY_PATH, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def load_user_history(user_id: str, limit: int = 10) -> list:
    """
    加载用户历史对话
    :param user_id: 用户 ID
    :param limit: 加载最近 N 条对话
    :return: 历史对话列表
    """
    try:
        user_dir = ensure_user_history_dir(user_id)
        history_file = os.path.join(user_dir, "history.json")

        if not os.path.exists(history_file):
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        # 返回最近的 limit 条对话
        return history[-limit:] if len(history) > limit else history
    except Exception as e:
        logger.error(f"[load_user_history]加载历史失败：{e}")
        return []


def save_user_history(user_id: str, role: str, content: str) -> None:
    """
    保存用户对话到历史
    :param user_id: 用户 ID
    :param role: 角色 ('human' 或 'ai')
    :param content: 对话内容
    """
    try:
        user_dir = ensure_user_history_dir(user_id)
        history_file = os.path.join(user_dir, "history.json")

        # 加载现有历史
        history = load_user_history(user_id, limit=100)

        # 添加新对话
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        history.append(new_message)

        # 保存到文件
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        logger.info(f"[save_user_history]保存用户 {user_id} 的历史对话")
    except Exception as e:
        logger.error(f"[save_user_history]保存历史失败：{e}")