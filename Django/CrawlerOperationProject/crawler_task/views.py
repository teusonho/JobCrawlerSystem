from django.shortcuts import render
from django.db.models import Q
from django.shortcuts import redirect
from .models import BossSpiderResultsBeat,BossSpiderResults

def items_root_redirect(request):
    """
    视图函数：重定向 /spider/ 到 /spider/items/
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