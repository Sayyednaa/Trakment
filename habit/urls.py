from django.urls import path
from . import views

urlpatterns = [
    path('', views.habit_list, name='habit_list'),
    path('habit/<int:habit_id>/', views.habit_detail, name='habit_detail'),
    path('habit/<int:habit_id>/update/<int:entry_id>/', views.habit_update, name='habit_update'),
    path('habit/<int:habit_id>/delete/<int:entry_id>/', views.habit_delete, name='habit_delete'),
]
