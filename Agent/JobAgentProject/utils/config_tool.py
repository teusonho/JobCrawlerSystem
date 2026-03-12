import yaml
from langchain_community.utilities import SQLDatabase

from utils.path_tool import get_abs_path


def load_model_config(config_path:str = get_abs_path("config/model.yml"),
                    encodeing:str="utf-8"):
    with open(config_path,"r", encoding=encodeing) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def load_prompts_config(config_path:str = get_abs_path("config/prompts.yml"),
                    encodeing:str="utf-8"):
    with open(config_path,"r", encoding=encodeing) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def load_agent_config(config_path:str = get_abs_path("config/agent.yml"),
                    encodeing:str="utf-8"):
    with open(config_path,"r", encoding=encodeing) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

model_conf = load_model_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()

def get_mysql_connection(table_name:str) -> SQLDatabase:
    db_conf = agent_conf["database"]
    db = SQLDatabase.from_uri(
        f"mysql+pymysql://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['name']}",
        include_tables=[table_name],
        engine_args={
            "pool_recycle": 3600,  # 每一小时自动重连，防止 MySQL "Server has gone away" 错误
            "pool_pre_ping": True  # 每次使用前检查连接是否存活
        },
    )
    return db
