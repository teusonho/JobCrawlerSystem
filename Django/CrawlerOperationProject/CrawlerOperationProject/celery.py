import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from django.conf import settings

# 设置 Django 的配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CrawlerOperationProject.settings')

app = Celery(
    "web_celery",
)

# 使用 Django 的配置文件来配置 Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'run-spider-daily_first': {
        'task': 'spider.send_boss_spider_beat',
        'schedule': crontab(hour=14, minute=00), # 每天 14:00 AM 执行
        'args': (['福州','厦门'], 30, 'python')
    },
    'run-spider-daily_test': {
        'task': 'spider.send_boss_spider_beat',
        'schedule': timedelta(seconds=30),      # 每 30 秒执行一次
        'args': ('福州', 5, 'python')
    },
}

# 自动发现任务
app.autodiscover_tasks(["crawler_task"])
