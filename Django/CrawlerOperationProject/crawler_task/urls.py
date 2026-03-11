from django.urls import path
from . import views

urlpatterns = [
    path('boss/beat', views.boss_spider_items_by_beat_view, name='boss_spider_items_by_beat'),
    path('boss/<str:task_id>/', views.boss_spider_items_by_task_id_view, name='boss_spider_items_by_task_id'),
    path('api/boss/createSpider', views.create_boss_spider_task_api, name='create_boss_spider_task_api'),
]