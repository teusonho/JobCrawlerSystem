import os
from abc import ABC, abstractmethod
from typing import Optional

from langchain_community.chat_models.tongyi import BaseChatModel, ChatTongyi
from langchain_core.embeddings import Embeddings
from langchain_ollama.chat_models import ChatOllama

from utils.config_tool import model_conf


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self)->Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(BaseModelFactory):
    def generator(self)->BaseChatModel:
        if int(model_conf["ollama_status"]):
            return ChatOllama(
                model=model_conf["chat_model_name"],
            )
        else:
            return ChatTongyi(
                api_key=os.getenv("DASHSCOPE_API_KEY"),     # 替换阿里云百炼的api key
                model=model_conf["chat_model_name"],
            )

chat_model = ChatModelFactory().generator()