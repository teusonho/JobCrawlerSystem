# Scrapy settings for JobCrawlerProject project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "JobCrawlerProject"

SPIDER_MODULES = ["JobCrawlerProject.spiders"]
NEWSPIDER_MODULE = "JobCrawlerProject.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32        # 并发数量

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3  # 并发请求延迟
RANDOMIZE_DOWNLOAD_DELAY  = True # 随机化下载延迟
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# 设置默认请求头
DEFAULT_REQUEST_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "JobCrawlerProject.middlewares.JobcrawlerprojectSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# 启动下载中间件
DOWNLOADER_MIDDLEWARES = {
    "JobCrawlerProject.middlewares.JobcrawlerprojectSpiderMiddleware": 543,
    "JobCrawlerProject.middlewares.LazyRequestMiddleware": 100, # 优先级调高
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# 启动管道，设置优先级，越小越优先
ITEM_PIPELINES = {
    "JobCrawlerProject.pipelines.JobcrawlerprojectPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

"""自定义设置"""
# 大于该级别的日志才会输出
LOG_LEVEL = 'INFO'
# 配置日志存放路径
import os
from datetime import datetime
LOG_FILE = os.path.join('JobCrawlerProject/logs', f"spider_{datetime.now().strftime('%Y%m%d')}.log")
# 日志模版：时间 - 日志器名称 - 日志级别 - 文件名:行号 - 日志内容
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
# 最大重试次数
MAX_RETRY_TIMES = 3
# 重试的延迟时间，每次递增
ORIGIN_RETRY_DELAY = 5
# 获取不到城市编码时，默认使用的城市编码
DEFAULT_CITY_CODES = {
    "zhipin" : {
        "北京":101010100,
        "上海":101020100,
    }
}
# 浏览器启动参数，需适配更改
BROWSER_CONNECT = 9222
# BROWSER_CONNECT = "C:\Program Files\Google\Chrome\Application\chrome.exe"
# MySQL连接串，需适配更改
MYSQL_DATABASE_URI = 'mysql+pymysql://root:abc123@localhost:3306/scrapy_job?charset=utf8mb4'
# celery中间件配置，需适配更改
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Redis 服务器地址
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1' # 任务结果存储在 Redis
CELERY_TIMEZONE = 'Asia/Shanghai'               # 设置服务器的时区