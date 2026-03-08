# admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import BossSpiderTask, BossSpiderResults
from .tasks import send_boss_spider_task  # 导入 Celery 任务

@admin.register(BossSpiderTask)
class BossSpiderTaskAdmin(ImportExportModelAdmin):
    list_display = ('id', 'domain', 'city', 'count', 'query', 'status', 'create_time', 'update_time',
                    'task_id', 'result', 'exception', 'query_items')
    list_display_links = ['id']
    fields = ('domain', 'city', 'count', 'query')
    readonly_fields = ('create_time', 'update_time', 'status', 'result', 'exception', 'task_id')    # 防止误修改状态和结果
    list_filter = ('domain', 'city','query', 'status')
    search_fields = ('domain', 'city', 'query', 'status')

    # 设置字段默认值
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None: # 如果是创建新对象
            form.base_fields['domain'].initial = 'zhipin.com'
            form.base_fields['city'].initial = '厦门'
            form.base_fields['count'].initial = 10
            form.base_fields['query'].initial = 'python'
        return form

    def query_items(self, obj):
        task_id = obj.task_id
        if task_id:
            url = f"/spider/{obj.task_id}/"  # 注意末尾的斜杠，与 URL 配置匹配
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.task_id)
        return "No items found"

    # 自定义操作：手动下发任务
    actions = ['run_spider']

    def run_spider(self, request, queryset):
        """Admin Action: 选中任务后运行爬虫"""
        for task_obj in queryset:
            # 检查任务状态，避免重复触发
            if task_obj.status == 'SUCCESS':
                self.message_user(request, f"Task {task_obj.id} executed.", level='WARNING')
                continue
            result = ""
            if "zhipin" in task_obj.domain:
                city = task_obj.city
                if ',' in city:
                    city = city.split(',')
                elif '，' in city:
                    city = city.split('，')
                count = task_obj.count
                query = task_obj.query
                result = send_boss_spider_task(city,count,query)
                # 保存 Celery 任务结果到数据库
                task_obj.update_time = timezone.now()
                task_obj.status = result.get("status")
                task_obj.result = result.get("result")
                task_obj.exception = result.get("exception")
                task_obj.task_id = result.get("task_id")
                task_obj.save(update_fields=['update_time', 'status', 'result', 'exception', 'task_id'])
                self.save_items(task_obj.task_id,result.get("items"))

            self.message_user(request, f"Started spider for task {task_obj.id}", level='SUCCESS')

    run_spider.short_description = "Run spider tasks"

    def save_items(self,task_id,items):
        for item in items:
            processed_item = item.copy()
            for field in ['skills', 'welfare']:
                if field in processed_item:
                    value = processed_item[field]
                    if isinstance(value, list):
                        processed_item[field] = ','.join(str(v) for v in value)

            BossSpiderResults.objects.create(
                task_id=task_id,  # 新增的 task_id 字段
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
            )
