import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import BossSpiderResultsBeat, BossSpiderResults, BossSpiderTask
from .tasks import send_boss_spider_task


def items_root_redirect(request):
    """
    视图函数：重定向 /spider/ 到 /spider/boss/beat/
    """
    return redirect('boss_spider_items_by_beat') # 使用目标 URL 的 name

def boss_spider_items_by_beat_view(request):
    """
    视图函数：处理 /items/beat/ 请求，展示 BossSpiderResultsBeat 数据，
    并支持按 name 模糊搜索和按 city, experience, scale 筛选。
    """
    # 开始查询所有数据
    items = BossSpiderResultsBeat.objects.all()

    # 获取查询参数
    query = request.GET.get('q', '') # 模糊搜索
    city_filter = request.GET.get('city', '')
    experience_filter = request.GET.get('experience', '')
    scale_filter = request.GET.get('scale', '')

    # 获取所有唯一的 city, experience, scale 值用于筛选器下拉菜单 (可选，提升用户体验)
    cities = BossSpiderResultsBeat.objects.values_list('city', flat=True).distinct().order_by('city')
    experiences = BossSpiderResultsBeat.objects.values_list('experience', flat=True).distinct().order_by('experience')
    scales = BossSpiderResultsBeat.objects.values_list('scale', flat=True).distinct().order_by('scale')


    # 应用模糊搜索 (name 字段)
    if query:
        items = items.filter(name__icontains=query) # icontains 不区分大小写

    # 应用 city 筛选
    if city_filter:
        items = items.filter(city__icontains=city_filter)

    # 应用 experience 筛选
    if experience_filter:
        items = items.filter(experience__icontains=experience_filter)

    # 应用 scale 筛选
    if scale_filter:
        items = items.filter(scale__icontains=scale_filter)

    context = {
        'items': items,
        'query': query,
        'city_filter': city_filter,
        'experience_filter': experience_filter,
        'scale_filter': scale_filter,
        'cities': cities,
        'experiences': experiences,
        'scales': scales,
    }
    return render(request, 'boss_spider_items.html', context)

def boss_spider_items_by_task_id_view(request, task_id):
    """
    根据 task_id 从 BossSpiderResults 获取数据并显示
    """
    # 从 BossSpiderResults 模型中筛选出 task_id 匹配的记录
    items = BossSpiderResults.objects.filter(task_id=task_id)

    # 检查是否有匹配的记录
    if not items.exists():
        # 如果没有找到对应的记录，可以选择渲染一个空模板或抛出 404 错误
        # 这里选择渲染一个带有提示的页面
        context = {
            'items': [],
            'task_id': task_id,
            'error_message': f"没有找到 task_id 为 '{task_id}' 的职位数据。"
        }
        return render(request, 'boss_spider_items.html', context)

    # 获取查询参数
    query = request.GET.get('q', '')
    city_filter = request.GET.get('city', '')
    experience_filter = request.GET.get('experience', '')
    scale_filter = request.GET.get('scale', '')

    # 获取去重的筛选选项 (基于当前 task_id 的数据)
    cities = items.values_list('city', flat=True).distinct().order_by('city')
    experiences = items.values_list('experience', flat=True).distinct().order_by('experience')
    scales = items.values_list('scale', flat=True).distinct().order_by('scale')


    # 应用模糊搜索 (name 字段)
    if query:
        items = items.filter(name__icontains=query)

    # 应用 city 筛选
    if city_filter:
        items = items.filter(city=city_filter)

    # 应用 experience 筛选
    if experience_filter:
        items = items.filter(experience=experience_filter)

    # 应用 scale 筛选
    if scale_filter:
        items = items.filter(scale=scale_filter)

    context = {
        'items': items,
        'task_id': task_id, # 将 task_id 传递给模板，方便显示或使用
        'query': query,
        'city_filter': city_filter,
        'experience_filter': experience_filter,
        'scale_filter': scale_filter,
        'cities': cities,
        'experiences': experiences,
        'scales': scales,
    }
    return render(request, 'boss_spider_items.html', context)


@csrf_exempt
def create_boss_spider_task_api(request):
    """
        API 接口：创建爬虫任务
        支持 GET 和 POST 两种方式
        GET: /spider/api/boss/createSpider?query=Java&city=北京&count=10
        POST: JSON body with {city, count, query}
        返回：JSON 格式的任务信息
        """
    try:
        # 处理 GET 请求
        if request.method == 'GET':
            city = request.GET.get('city')
            count = request.GET.get('count', '10')
            query = request.GET.get('query', 'python')

        # 处理 POST 请求
        else:
            data = json.loads(request.body)
            city = data.get('city')
            count = data.get('count', '10')
            query = data.get('query', 'python')

        # 验证 count 是否为整数
        try:
            count = int(count)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'count must be an integer'
            }, status=400)

        # 创建数据库记录（初始状态为 PENDING）
        task_entry = BossSpiderTask.objects.create(
            domain='zhipin.com',
            city=city,
            count=count,
            query=query,
            status='PENDING'
        )

        # 异步执行 Celery 任务
        celery_result = send_boss_spider_task(city, count, query)

        # 更新数据库记录
        task_entry.status = celery_result.get('status')
        task_entry.result = str(celery_result.get('result'))
        task_entry.exception = str(celery_result.get('exception', ''))[:100]
        task_entry.task_id = celery_result.get('task_id')
        task_entry.save(update_fields=['status', 'result', 'exception', 'task_id'])

        # 保存爬取结果到 BossSpiderResults
        items = celery_result.get('items', [])
        for item in items:
            processed_item = item.copy()
            for field in ['skills', 'welfare']:
                if field in processed_item:
                    value = processed_item[field]
                    if isinstance(value, list):
                        processed_item[field] = ','.join(str(v) for v in value)

            BossSpiderResults.objects.create(
                task_id=celery_result.get('task_id'),
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
                keyword=query,
            )

        return JsonResponse({
            'success': True,
            'data': {
                'task_id': task_entry.task_id,
                'db_id': task_entry.id,
                'status': task_entry.status,
                'result_count': celery_result.get('result'),
                'city': city,
                'count': count,
                'query': query
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
