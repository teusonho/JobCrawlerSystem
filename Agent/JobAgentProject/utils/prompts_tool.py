from utils.config_tool import prompts_conf
from utils.logger_tool import logger
from utils.path_tool import get_abs_path


def load_system_prompt():
    """ 加载系统提示词 """
    try:
        system_prompt_path = get_abs_path(prompts_conf['main_prompt_path'])
    except KeyError as e:
        logger.error("请检查配置文件，缺少main_prompt_path字段")
        raise e
    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except Exception as e:
        logger.error(f"加载系统提示词失败：{str(e)}")
        raise e

