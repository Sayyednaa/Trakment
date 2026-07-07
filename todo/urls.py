from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('update/<int:pk>/', views.task_update, name='task_update'),
    path('delete/<int:pk>/', views.task_delete, name='task_delete'),
    path('toggle/<int:pk>/', views.task_toggle, name='task_toggle'),
    path('syllabus/', views.syalfun, name='syllabus'),
    path('syllabus/add/', views.syal_add, name='syal_add'),
    path('syllabus/update/<int:id>/', views.syal_update, name='syal_update'),
    path('syllabus/delete/<int:id>/', views.syal_delete, name='syal_delete'),
]