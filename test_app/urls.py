from django.urls import path
from . import views

app_name = 'test'
urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add, name='add'),
    path('update/<int:id>/', views.update, name='update'),
    path('delete/<int:id>/', views.delete, name='delete'),
    path('save-test/', views.self_test, name='save_test'),
    path('chapter/<int:chapter_id>/analytics/', views.chapter_analytics, name='chapter_analytics'),
    path('self-test/', views.self_test, name='self_test'),
    path('self-test/<int:id>/', views.self_test_detail, name='self_test_detail'),
    path('self-test/analysis/', views.self_test_analysis, name='self_test_analysis'),
    path('self-tests/', views.self_test_analysis, name='self_tests'),
    path('self-test/statistics/', views.self_tests_statistics, name='self_tests_statistics'),
    path('self-test/delete/<int:id>/', views.delete_self_test, name='delete_self_test'),
    path('self-test/delete-alias/<int:id>/', views.delete_self_test, name='self_test_delete'),
]