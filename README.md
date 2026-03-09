# 基于Django+Scrapy的爬虫系统采集Boss直聘岗位列表

## 1.功能介绍

该系统主要用于采集boss直聘的岗位信息，基于Django框架搭建web端，基于Scrapy框架搭建爬虫端，二者通过celery中间件和Redis消息队列通信。

### 1.1 web端功能

进入admin界面，通过以下方式下发爬虫任务：

(1)新建；(2)批量导入；(3)celery定时下发；(4)API下发，支持GET和POST请求，URL格式：/spider/api/create-task?query=python&city=北京&count=20。

批量导入参考“Django\CrawlerOperationProject\爬虫任务模版.csv”文件。
domain字段默认zhipin.com；
city字段可填写多城市，使用中文逗号"，"或英文逗号","做分隔符（不支持混用）；
count字段表示每个城市爬取多少岗位；
query字段用于boss直聘搜索。

通过celery beat定时下发爬虫任务。

爬虫任务下发后生成任务ID，可通过URL查询该任务的采集详情，如下图。

![image-20260308234836368](https://github.com/teusonho/CrawlerSystem/blob/main/README_pic/spider_detail.png)

### 1.2 爬虫端功能

爬虫端接收到任务

(1)启动浏览器访问boss直聘获取cookie；
(2)采用POST发包获取对应城市编码；
(3)解析后再携带参数重新发包获取岗位列表，得到为失败响应则延迟重试步骤(1)(3)，直到成功或达到最大尝试次数；
(4)任务结束后保存Mysql数据库并通过消息队列redis返回。

## 2.配置

系统分为两个项目分别部署。

### 2.1 web端配置

Django项目需修改，\CrawlerOperationProject\CrawlerOperationProject\settings.py文件以下参数，用于配置Mysql和Redis，采集的岗位信息有web端和爬虫端双端存储。

```
DATABASES
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
```

celery beat定时下发的任务，需设置CrawlerOperationProject\celery.py文件

### 2.2爬虫端配置

Scrapy项目需修改，\JobCrawlerProject\JobCrawlerProject\settings.py文件以下参数，用于配置浏览器、Mysql和Redis，配置的edge或chrome浏览器需保留登录账户。

```
BROWSER_CONNECT
MYSQL_DATABASE_URI
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
```

## 3.启动

### 3.1 web端启动

进入Django项目的CrawlerOperationProject目录下（manage.py所在目录），激活虚拟环境。

执行迁移

```
python manage.py makemigrations
python manage.py migrate
```

启动服务器，默认为127.0.0.01本机的8000端口

```
python manage.py runserve
```

启动celery worker，用于发送爬虫任务，-Q参数指定监听队列spider.tasks_queue

```
celery -A CrawlerOperationProject worker -l info -P solo -Q spider.tasks_queue
```

启动celery beat定时下发爬虫任务，可不启动

```
celery -A CrawlerOperationProject beat -l info
```

### 3.2 爬虫端启动

进入Scrapy项目的JobCrawlerProject目录下（celery_worker.py所在目录），激活虚拟环境。

测试可通过main.py代码单独运行爬虫

启动celery worker，用于接收爬虫任务，-Q参数指定监听队列spider.tasks_queue

```
celery -A celery_worker worker -l info -P solo -Q spider.worker_queue
```

## 4. 安全说明

本项目仅供**学术研究**与**教育测试**之用。使用者在下载或使用时，即表示同意以下条款：

- **合规性责任**：使用者必须遵守所在地法律法规以及目标网站的协议、使用条款。
- **禁止用途**：严禁将本项目用于任何非法目的，包括但不限于：非法侵入他人系统、破坏网络安全、非法获取敏感个人数据、进行不正当商业竞争。
- **后果自负**：开发者不承担因用户违规使用导致的任何法律责任（包括但不限于民事、行政或刑事责任）。

为了维护互联网生态，本工具建议遵循以下原则：

- **频率限制**：请设置合理的下载延迟，避免对目标服务器造成过大压力（即拒绝服务攻击）。
- **尊重隐私**：请勿尝试抓取非公开的个人敏感信息或涉及国家安全的数据。
- **版权尊重**：抓取到的数据仅供学习参考，未经授权不得用于商业转售或侵犯知识产权的行为。

## 5.反爬

boss直聘网站开启了反爬措施，包括但不限于以下措施：

25年12月还可以只使用访客cookie（即免登录）获取岗位信息，后禁用，并限制每个响应包的岗位数量由30减至15。

本项目未加入逆向措施，用于破解boss直聘的极验验证码登录，无法破解获取cookie中关键的'__zp_token__'字段。

boss直聘25年12月下旬开启了浏览器反调试，在edge和chrome打开开发者工具会触发页面闪退无法获取响应包，可更换firefox火狐浏览器调试。

项目代码预留了爬取岗位详情的内容，暂时注释掉，原因为爬取岗位详情时，需要对每个岗位链接都发送请求，极易触发IP风控，并一并注释Django项目中的description岗位描述和address_detail详细地址字段。

