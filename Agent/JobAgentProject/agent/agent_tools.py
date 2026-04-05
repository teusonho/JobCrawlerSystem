from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Any, List

import requests
from langchain_classic.agents.mrkl.prompt import FORMAT_INSTRUCTIONS
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool, tool
from sqlalchemy import text

from model.factory import chat_model
from utils.config_tool import agent_conf, get_mysql_connection
from utils.logger_tool import logger
from utils.prompts_tool import load_query_prompt

# 初始化数据库连接
JOB_INFO_DB = get_mysql_connection("boss_spider_results")


class SlimSQLDatabaseToolkit(SQLDatabaseToolkit):
    """仅暴露「执行 SQL」工具：表结构通过 prompt 注入，避免每次 list_tables / schema / checker。"""

    def get_tools(self) -> List[BaseTool]:
        return [
            QuerySQLDatabaseTool(
                db=self.db,
                description=(
                    "输入：语法正确的 SELECT 语句（仅查询，禁止 DML）。"
                    "输出：查询结果文本；若报错，根据系统提示中的表结构修正 SQL 后重试。"
                ),
            )
        ]


@lru_cache(maxsize=8)
def _build_sql_agent_executor(prefix_template: str, suffix_template: str):
    """
    按给定 query 提示词模板构建 SQL Agent（进程内缓存多组模板便于切换场景）。
    表结构在构建时写入 prompt；修改 prompts/query_prompt.txt 后需 cache_clear 或换用新模板字符串。
    """
    toolkit = SlimSQLDatabaseToolkit(llm=chat_model, db=JOB_INFO_DB)
    template = "\n\n".join(
        [
            prefix_template,
            "{tools}",
            FORMAT_INSTRUCTIONS,
            suffix_template,
        ]
    )
    prompt = PromptTemplate.from_template(template)
    return create_sql_agent(
        llm=chat_model,
        toolkit=toolkit,
        agent_type="zero-shot-react-description",
        prompt=prompt,
        verbose=False,
        max_iterations=6,
        handle_parsing_errors=True,
    )


def get_job_sql_agent_executor(
    query_prefix: str | None = None,
    query_suffix: str | None = None,
):
    """
    获取 SQL 子 Agent。默认从 prompts/query_prompt.txt 加载；切换场景可传入自定义前后缀模板
   （须保留 {dialect}、{top_k}、{table_info} 与 {input}、{agent_scratchpad} 等占位符）。
    """
    if query_prefix is None or query_suffix is None:
        query_prefix, query_suffix = load_query_prompt()
    return _build_sql_agent_executor(query_prefix, query_suffix)


def clear_job_sql_agent_cache() -> None:
    """清空 SQL Agent 缓存（例如热更新了 query 提示词文件后）。"""
    _build_sql_agent_executor.cache_clear()

@tool(description="采集岗位信息，获取采集结果和任务ID")
def crawl_job_info(query: str, website: str = "boss", city: str | list[str] = "厦门", count: int = 30) -> Dict[
    str, Any]:
    """
    爬取岗位信息的API
    :param
    - query: 查询关键词 (如 'Java')
    - website: 网站（入 'boss'）
    - city: 城市 (如 '北京')
    - count: 数量 (默认10)
    """
    url = f"{agent_conf["system_domain"]}/spider/api/{website}/createSpider?query={query}&city={city}&count={count}"

    try:
        logger.info(f"[crawl_job_info]启动爬虫: website:{website},query:{query},city:{city},count:{count}")
        response = requests.get(url)
        result = response.json()
        logger.info(f"[crawl_job_info]爬虫结果: result.get('success')")
        if result.get('success'):
            # 等待爬取完成
            return {
                'success': True,
                'status': result['data'].get('status'),
                'content': result['data'].get('task_id'),
            }
        else:
            return {
                'success': False,
                'status': response.status_code,
                'content': result.get('error'),
            }
    except Exception as e:
        logger.error(f"[crawl_job_info]爬虫失败: {e}")
        return {
            'success': False,
            'content': str(e)
        }


@tool(description="查询历史爬虫任务 ID，根据关键词和城市获取指定日期内的任务 ID 列表")
def get_task_ids(keyword: str, city: str | list[str], days_ago: int = 7, date: str = "") -> list[str]:
    """
    查询历史爬虫任务 ID
    :param:
    - keyword: 岗位关键词 (如 'Java', 'Python')
    - city: 筛选城市
    - day_ago: 筛选多少天前
    - date: 筛选日期 ('2026-01-01')
    :return:
    - 任务 ID 列表
    """
    if isinstance(city,str):
        city = [city]
    city = tuple(city)
    if not date:
        date = datetime.now() - timedelta(days=days_ago)

    query = text("""
                 SELECT DISTINCT task_id
                 FROM boss_spider_results
                 WHERE LOWER(keyword) LIKE :kw
                   AND city in :city
                   AND created_at >= :date
                 """)
    try:
        with JOB_INFO_DB._engine.connect() as conn:

            logger.info(f'[get_task_ids]查询历史任务: kw:{keyword}, city:{city}, days_ago:{days_ago}, date:{date}')
            result = conn.execute(query, {"kw": f"%{keyword.strip().lower()}%", "city":city, "date": date})
            # 使用列表推导式，row[0] 即为 task_id
            return [row[0] for row in result if row[0]]
    except Exception as e:
        # 这里建议加上你的日志记录
        logger.error(f"[get_task_ids]查询历史任务出错: {e}")
        return []


@tool(description="查询本地数据库中的岗位信息。可以按任务ID、职位名称、城市、经验、学历等条件筛选和分析历史采集数据。支持模糊查询、统计分析和数据对比。")
def query_job_database(query_str: str) -> str:
    """
    查询本地 MySQL 数据库中的岗位信息
    :param
    - query_str: 自然语言查询请求，如"查找厦门的 Python 岗位"

    :return
    - 查询结果及分析
    """
    try:
        sql_agent = get_job_sql_agent_executor()
        logger.info(f"[query_job_database]查询岗位信息: {query_str}")
        result = sql_agent.invoke({"input": query_str})
        return result.get("output", "查询未返回结果")

    except Exception as e:
        logger.error(f"[query_job_database]查询历史任务出错: {e}")
        return f"数据库查询失败：{str(e)}"

