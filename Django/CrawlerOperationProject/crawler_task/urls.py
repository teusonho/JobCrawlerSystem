from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.boss_spider_items_by_beat_view, name='boss_spider_items_by_beat'),
    path('<str:task_id>/', views.boss_spider_items_by_task_id_view, name='boss_spider_items_by_task_id'),
]