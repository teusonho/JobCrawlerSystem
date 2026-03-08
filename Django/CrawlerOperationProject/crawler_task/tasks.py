import time
import json
import logging

from CrawlerOperationProject.celery import app
from .models import BossSpiderResultsBeat

logger = logging.getLogger(__name__)

@app.task(name='spider.send_boss_spider',queue = 'spider.tasks_queue')
def send_boss_spider_task(city,count,query):
    target_task_name = 'spider.run_boss_spider'
    r = app.send_task(
        target_task_name,
        args=[
            city, count, query
        ],
        queue='spider.worker_queue'
    )
    while not r.ready():
        time.sleep(1)
    result = r.result
    data = {}
    data["task_id"] = r.id
    data["status"] = "SUCCESS" if result.get("success") else "FAILURE"
    data["result"] = len(result.get("items"))
    data["exception"] = result.get("exception")[:30]
    data["items"] = result.get("items")
    return data

@app.task(name='spider.send_boss_spider_beat', queue='spider.tasks_queue') # 指定队列
def send_boss_spider_beat(city, count, query):
    result_data = send_boss_spider_task(city, count, query)
    items = result_data.get("items", [])
    deleted_count, _ = BossSpiderResultsBeat.objects.all().delete()
    logger.info(f"Deleted {deleted_count} existing records.")
    for processed_item in items:
        # processed_item = item.copy()  # 避免修改原始 item
        for field in ['skills', 'welfare']:  # 假设 LIST_FIELDS 是 ['skills', 'welfare']
            if field in processed_item:
                value = processed_item[field]
                if isinstance(value, list):
                    processed_item[field] = ','.join(str(v) for v in value)

        # 创建 Django 模型实例并保存
        boss_result_entry = BossSpiderResultsBeat.objects.create(
            name=processed_item.get('name', ''),
            link=processed_item.get('link', ''),
            boss_name=processed_item.get('boss_name', ''),
            boss_title=processed_item.get('boss_title', ''),
            salary=processed_item.get('salary', ''),
            skills=processed_item.get('skills', ''),
            experience=processed_item.get('experience', ''),
            degree=processed_item.get('degree', ''),
            city=processed_item.get('city', ''),
            area=processed_item.get('area', ''),
            address=processed_item.get('address', ''),
            company=processed_item.get('company', ''),
            scale=processed_item.get('scale', ''),
            welfare=processed_item.get('welfare', ''),
            # description=processed_item.get('description', ''),
            # address_detail=processed_item.get('address_detail', ''),
            # Django 模型会自动处理 created_at 和 updated_at
        )
    return result_data