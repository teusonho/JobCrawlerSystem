import json
import math
from urllib.parse import urlencode

import scrapy
import cpca

from ..items import JobItem
from scrapy.utils.project import get_project_settings


class BossSpider(scrapy.Spider):
    name = "bossSpider"
    allowed_domains = ["www.zhipin.com"]

    def __init__(self, city: str|list = "", count=30, query='python', salary=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.city = city
        self.count = int(count)
        self.query = query
        self.salary = salary
        self.city_codes = {}
        self.max_retry_times = get_project_settings().get("MAX_RETRY_TIMES",0)
        self.origin_retry_delay = get_project_settings().get("ORIGIN_RETRY_DELAY",0)
        self.default_city_codes = get_project_settings().get("DEFAULT_CITY_CODES",{})

    def start_requests(self):
        yield self._get_city_codes()

    def _get_city_codes(self):
        """
        发起对城市编码的请求
        """
        city_api_url = "https://www.zhipin.com/wapi/zpgeek/common/data/city/site.json"
        return scrapy.Request(url=city_api_url, callback=self._handle_city_codes_response, dont_filter=True)

    def _handle_city_codes_response(self, response):
        """
        携带城市编码的参数发起职位列表的请求
        """
        try:
            data = json.loads(response.text)
            if data.get("message") == "Success":
                self.city_codes = data.get("zpData").get("siteList")
        except Exception as e:
            self.logger.error(f"[BossSpider]解析城市编码失败，使用默认城市: {e}")
        # 当城市参数为字符串时
        if self.city and isinstance(self.city,str) and self.city_codes:
            city_name = self.city
            city_code = self._handle_city(self.city)
            if not city_code:
                self.logger.error(f"[BossSpider]城市编码错误: {city_name}")
            else:
                city_dict = {
                    city_name:city_code
                }
        # 当城市参数为列表时
        elif self.city and isinstance(self.city,list) and self.city_codes:
            city_dict = {}
            for city_name in self.city:
                city_code = self._handle_city(city_name)
                if not city_code:
                    self.logger.error(f"[BossSpider]城市编码错误: {city_name}")
                    break
                else:
                    city_dict[city_name] = city_code
        else:
            city_dict = self.default_city_codes.get("zhipin",{})
        count = self.count          # 岗位数量
        self.logger.info(f"[BossSpider]城市参数:{city_dict}")
        for city,city_code in city_dict.items():
            if city_code == "":
                continue
            remainder = count
            limit = 15
            for i in range(math.ceil(count/limit)):
                params = {
                    "city": str(city_code),
                    "query": self.query,              # 搜索
                    "jobType": str(1901),             # 求职类型：全职
                }
                job_list_url = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
                # job_list_url = "https://www.zhipin.com/wapi/zpgeek/pc/recommend/job/list.json"
                params["page"] = str(i+1)
                params["pageSize"]= str(limit) if remainder >= limit else str(remainder)
                if remainder >= limit:
                    remainder -= limit
                self.logger.info(f"[BossSpider]请求参数:{params}")
                self.logger.info(f"[BossSpider]请求URL:{job_list_url}")
                yield scrapy.FormRequest(
                    url = job_list_url,
                    callback=self.parse,
                    formdata=params,
                    dont_filter=True,
                    meta={"formdata":params}
                )

    def _handle_city(self,city):
        """
        解析获取城市编码
        """
        if not self.city_codes:
            return ""
        else:
            df = cpca.transform([city])
            province_name = df['省'].iloc[0]
            if "省" in province_name:
                province_name = province_name[:-1]
            else:
                province_name = province_name[:2]
            for province_item in self.city_codes:
                if province_item.get("name") == province_name:
                    for city_item in province_item.get("subLevelModelList"):
                        if city_item.get("name") == city:
                            return city_item.get("code")
        return ""

    def parse(self, response, **kwargs):
        """处理职位列表"""
        retry_times = response.meta.get('retry_times', 1)
        retry_delay = response.meta.get('retry_delay',self.origin_retry_delay)
        data = json.loads(response.text)
        if data.get("message") == "Success":
            """解析职位列表"""
            # yield self._parse_list(data)
            jobs = data.get("zpData", {}).get("jobList", [])
            for job in jobs:
                job_item = JobItem()
                slug = job.get("encryptJobId")
                job_item["link"] = f"https://www.zhipin.com/job_detail/{slug}.html"
                job_item["name"] = job.get("jobName")
                job_item["boss_name"] = job.get("bossName")
                job_item["boss_title"] = job.get("bossTitle")
                job_item["salary"] = job.get("salaryDesc")
                job_item["skills"] = job.get("skills")
                job_item["experience"] = job.get("jobExperience")
                job_item["degree"] = job.get("jobDegree")
                job_item["city"] = job.get("cityName")
                job_item["area"] = job.get("areaDistrict")
                job_item["address"] = job.get("businessDistrict")
                job_item["company"] = job.get("brandName")
                job_item["scale"] = job.get("brandScaleName")
                job_item["welfare"] = job.get("welfareList")
                params = {
                    "securityId": job.get("securityId"),
                    "lid": job.get("lid")
                }
                job_detail_url = f"https://www.zhipin.com/wapi/zpitem/web/competitive/jobDetail.json"
                # job_detail_url = f"https://www.zhipin.com/wapi/zpgeek/job/detail.json"
                self.logger.info(f"[BossSpider]爬取岗位列表:{job_detail_url}")
                # todo:预留爬取岗位详情的功能，由于对岗位列表的每个链接批量爬取，易触发boos直聘网的反爬措施，造成IP被封或触发机器人验证，需逆向解决
                job_detail_url = job_detail_url + "?" + urlencode(params)
                # yield scrapy.Request(url=job_detail_url, callback=self.parse_job, meta={'item': job_item})
                yield job_item
        else:
            self.logger.warning(
                f"[BossSpider]API failed (message={data.get("message")}) on {response.url}, "
            )
            yield self._retry(response, retry_times, retry_delay)

    def _parse_list(self,data):
        """解析职位列表"""
        jobs = data.get("zpData", {}).get("jobList", [])
        for job in jobs:
            job_item = JobItem()
            slug = job.get("encryptJobId")
            job_item["link"] = f"https://www.zhipin.com/job_detail/{slug}.html"
            job_item["name"] = job.get("jobName")
            job_item["boss_name"] = job.get("bossName")
            job_item["boss_title"] = job.get("bossTitle")
            job_item["salary"] = job.get("salaryDesc")
            job_item["skills"] = job.get("skills")
            job_item["experience"] = job.get("jobExperience")
            job_item["degree"] = job.get("jobDegree")
            job_item["city"] = job.get("cityName")
            job_item["area"] = job.get("areaDistrict")
            job_item["address"] = job.get("businessDistrict")
            job_item["company"] = job.get("brandName")
            job_item["scale"] = job.get("brandScaleName")
            job_item["welfare"] = job.get("welfareList")
            params = {
                "securityId": job.get("securityId"),
                "lid": job.get("lid")
            }
            job_detail_url = f"https://www.zhipin.com/wapi/zpitem/web/competitive/jobDetail.json"
            # job_detail_url = f"https://www.zhipin.com/wapi/zpgeek/job/detail.json"
            self.logger.info(f"[BossSpider]爬取岗位列表:{job_detail_url}")
            # todo:预留爬取岗位详情的功能，由于对岗位列表的每个链接批量爬取，易触发boos直聘网的反爬措施，造成IP被封或触发机器人验证，需逆向解决
            job_detail_url = job_detail_url + "?" + urlencode(params)
            # yield scrapy.Request(url=job_detail_url, callback=self.parse_job, meta={'item': job_item})
            yield job_item

    def _retry(self, response, retry_times, retry_delay):
        """构造重试请求，计算下一次的延迟"""
        if retry_times >= self.max_retry_times:
            self.logger.error(f"达到最大重试次数，放弃: {response.url}")
            return

        # 每次延迟递增
        next_delay = retry_delay + self.origin_retry_delay

        # 提取原始 formdata (如果是 POST 请求)
        form_data = response.request.meta.get('formdata')
        self.logger.info(f"retry {retry_times}/{self.max_retry_times}\n将在 {retry_delay} 秒后重试...")
        return scrapy.FormRequest(
            url=response.request.url,
            formdata=form_data,
            callback=self.parse,
            dont_filter=True,  # 防止重试请求被过滤
            meta={
                'retry_times': retry_times + 1,
                'retry_delay': next_delay,  # 传递给下一次的重试
                'formdata': form_data,
                'target_delay': retry_delay  # 告诉中间件这次要等多久
            },
            priority=10  # 提高优先级，确保重试请求优先处理
        )

    def parse_job(self, response):
        """处理职位详情"""
        data = json.loads(response.text)
        if data.get("message") == "Success":
            job_info = data.get("zpData",{}).get("jobInfo",{})
            job_item = response.meta['item']
            job_item["description"] = job_info.get("postDescription")
            job_item["address_detail"] = job_info.get("address")
            yield job_item
