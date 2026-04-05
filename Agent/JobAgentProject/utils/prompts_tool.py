from utils.config_tool import prompts_conf
from utils.logger_tool import logger
from utils.path_tool import get_abs_path

# query_prompt.txt 中前缀段与 ReAct 后缀段的分隔行（独占一行）
QUERY_PROMPT_SECTION_SPLIT = "---SQL_SUFFIX---"


def _read_prompt_file(relative_path: str) -> str:
    path = get_abs_path(relative_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载提示词文件失败 {relative_path}：{e}")
        raise


def load_main_prompt() -> str:
    """加载主 Agent 系统提示词（prompts/main_prompt.txt，路径可由 prompts.yml 配置）。"""
    rel = prompts_conf.get("main_prompt_path", "prompts/main_prompt.txt")
    return _read_prompt_file(rel)


def load_system_prompt() -> str:
    """兼容旧接口，等同于 load_main_prompt。"""
    return load_main_prompt()


def load_query_prompt() -> tuple[str, str]:
    """
    加载 SQL 子 Agent 的提示词模板：返回 (prefix_template, suffix_template)。
    文件由 prompts.yml 的 query_prompt_path 指定，内含占位符
    {dialect}、{top_k}、{table_info}（前缀）及 {input}、{agent_scratchpad}（后缀）。
    """
    rel = prompts_conf.get("query_prompt_path", "prompts/query_prompt.txt")
    raw = _read_prompt_file(rel)
    if QUERY_PROMPT_SECTION_SPLIT not in raw:
        logger.error(
            f"query 提示词文件中缺少分隔行 {QUERY_PROMPT_SECTION_SPLIT!r}，"
            "请在该行上方写前缀、下方写 ReAct 后缀。"
        )
        raise ValueError(f"无效的 query 提示词格式：{rel}")
    prefix, suffix = raw.split(QUERY_PROMPT_SECTION_SPLIT, 1)
    return prefix.strip(), suffix.strip()
