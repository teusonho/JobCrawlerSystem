import sys
import os
import json
import subprocess
from celery import Celery
from scrapy.utils.project import get_project_settings

# 初始化 Celery
settings = get_project_settings()
app = Celery("spider_celery_work")
app.conf.update(
    broker_url=settings.get("CELERY_BROKER_URL"),
    result_backend=settings.get("CELERY_RESULT_BACKEND"),
    timezone=settings.get("CELERY_TIMEZONE"),
    enable_utc=False,
)


@app.task(name='spider.run_boss_spider', queue='spider.worker_queue')
def run_boss_task(city, count, query):
    # 将爬虫逻辑编写为一段独立的 Python 代码字符串
    # 使用 json.dumps 确保参数安全地传递进字符串
    script = f"""
import json
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from pydispatch import dispatcher
# 确保子进程能找到你的项目
import sys
sys.path.append(r'{os.getcwd()}')
from JobCrawlerProject.spiders.bossSpider import BossSpider

def start_crawl():
    items = []
    def item_scraped(item):
        items.append(dict(item))

    settings = get_project_settings()
    # 可以在这里关闭日志输出，避免干扰标准输出
    settings.set('LOG_ENABLED', False) 

    process = CrawlerProcess(settings)
    dispatcher.connect(item_scraped, signal=signals.item_scraped)

    process.crawl(BossSpider, city={json.dumps(city)}, count={json.dumps(count)}, query={json.dumps(query)})
    process.start()

    # 将结果打印到标准输出，以便主进程捕获
    print(json.dumps(items))

if __name__ == "__main__":
    start_crawl()
"""

    try:
        # 启动全新的 Python 子进程执行字符串代码
        # sys.executable 获取当前 Python 解释器的路径
        process = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            # 解析子进程打印的 JSON 数据
            items = json.loads(stdout.strip())
            return {"success": True if len(items) > 0 else False,
                    "items": items,
                    "exception": ""
                    }
        else:
            return {
                "success": False,
                "items": [],
                "exception": stderr
            }

    except Exception as e:
        return {
            "success": False,
            "items": [],
            "exception": str(e)
        }

if __name__ == '__main__':
    pass