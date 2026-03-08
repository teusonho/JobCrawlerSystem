# 过滤pkg_resources警告
import warnings
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated as an API.*", category=UserWarning)

from pydispatch import dispatcher
from scrapy import cmdline
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from JobCrawlerProject.spiders.bossSpider import BossSpider

settings = get_project_settings()


def run_boss_spider_by_cmdline(city: str = "", count=10, query=""):
    """使用命令行启动spider，只接收单城市字符串"""
    command = "scrapy crawl bossSpider"
    args = {
        "city": city,
        "count": count,
        "query": query
    }
    for key, value in args.items():
        if value:
            command += f" -a {key}={value}"

    print(command)
    cmdline.execute(command.split())


def run_boss_spider(city: str | list = "", count=10, query=""):
    """使用scrapy的引擎启动spider"""
    items = []
    exception_msg = ""

    # 定义信号处理函数，将爬取到的 item 存入列表
    def item_passed(item, response, spider):
        items.append(dict(item))

    # 将信号与处理函数绑定
    dispatcher.connect(item_passed, signal=signals.item_scraped)

    try:
        # 获取 Scrapy 设置
        process = CrawlerProcess(settings=settings)

        # 启动 Spider，并传递你需要的参数
        process.crawl(BossSpider, city=city, count=count, query=query)

        # 启动引擎（此操作会阻塞，直到爬虫完成）
        process.start()

    except Exception as e:
        exception_msg = str(e)

    success = lambda items: True if bool(len(items)) else False
    # 返回最终构造的数据格式
    return {
        "success": success,
        "items": items,
        "exception": exception_msg
    }


# 使用示例
if __name__ == "__main__":
    result = run_boss_spider(city="杭州", count=5, query="python")
    print(f"成功: {result['success']}")
    print(f"爬取数量: {len(result['items'])}")
    for item in result['items']:
        print(item)
