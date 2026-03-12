from langchain.agents import create_agent

from agent.agent_middleware import tool_monitor, log_before_model
from agent.agent_tools import crawl_job_info,get_task_ids, query_job_database
from model.factory import chat_model
from utils.prompts_tool import load_system_prompt


class AgentReact:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.agent = create_agent(
            model=chat_model,
            tools=[crawl_job_info,get_task_ids, query_job_database],
            middleware=[tool_monitor, log_before_model],
            system_prompt=load_system_prompt(),
        )

    def execute_stream(self, query: str, history: list = None):
        """
        执行对话（支持历史上下文）
        :param query: 当前用户输入
        :param history: 历史对话列表
        """
        # 构建消息列表
        messages = []

        # 如果有历史对话，添加到消息中
        if history:
            for msg in history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # 添加当前用户输入
        messages.append({"role": "user", "content": query})

        input_dict = {"messages": messages}

        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            lastest_message = chunk["messages"][-1]
            if lastest_message:
                if lastest_message:
                    # 处理 content 可能是列表的情况
                    content = lastest_message.content

                    if isinstance(content, list):
                        # 如果是列表，提取所有文本内容并拼接
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict):
                                text_parts.append(item.get("text", ""))
                            elif isinstance(item, str):
                                text_parts.append(item)
                        content = "".join(text_parts)

                    # 确保 content 是字符串
                    if isinstance(content, str):
                        yield content.strip() + "\n"


if __name__ == '__main__':
    agent = AgentReact()
    input_data = "我想找福州的python工程师岗位"
    for chunk in agent.execute_stream(input_data):
        print(chunk, end="", flush=True)
