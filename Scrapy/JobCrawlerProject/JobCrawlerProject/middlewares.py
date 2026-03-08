# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# useful for handling different item types with a single interface

import json

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from twisted.internet import reactor
from twisted.internet.task import deferLater

from .utils.activate_chrome import *


class JobcrawlerprojectSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self):
        self.browser = create_chrome()
        self.boss_cookies = ""

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        # 处理爬取boss直聘网的请求
        if "zhipin.com" in request.url:
            if not self.boss_cookies:
                self.boss_cookies = get_cookies_by_boss(self.browser)
            # 判断是否为延迟请求，重新获取cookies
            delay = request.meta.get('target_delay')
            if delay:
                self.boss_cookies = get_cookies_by_boss(self.browser)
            cookies = self.boss_cookies
            # 处理岗位列表请求
            if "search/joblist" in request.url:
                if not cookies or (isinstance(cookies, dict) and not cookies):
                    spider.logger.warning(f"[process_request]岗位列表请求被取消：cookies 为空，URL={request.url}")
                    raise IgnoreRequest("Cookies is empty, request cancelled.")
                else:
                    request.cookies = cookies
                    return None
            # 处理岗位列表请求
            elif "job/detail" in request.url:
                if not cookies or (isinstance(cookies, dict) and not cookies):
                    spider.logger.warning(f"[process_request]岗位详情请求被取消：cookies 为空，URL={request.url}")
                    raise IgnoreRequest("Cookies is empty, request cancelled.")
                else:
                    request.cookies = cookies
                    return None
            # 处理城市编码请求
            elif "data/city" in request.url:
                if not cookies or (isinstance(cookies, dict) and not cookies):
                    spider.logger.warning(f"[process_request]城市编码请求被取消：cookies 为空，URL={request.url}")
                    raise IgnoreRequest("Cookies is empty, request cancelled.")
                else:
                    request.cookies = cookies
                    return None
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class LazyRequestMiddleware:
    """专门处理 Request meta 中指定的延迟"""
    def process_request(self, request, spider):
        delay = request.meta.get('target_delay')
        if delay:
            # 使用 deferLater 实现非阻塞等待
            # 这会让 Scrapy 引擎知道这个请求在“处理中”，从而不会关闭爬虫
            d = deferLater(reactor, delay, lambda: None)
            return d
        return None