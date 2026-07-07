from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-lecture/', views.add_lecture, name='add_lecture'),
    path('edit-lecture/<int:lecture_id>/', views.edit_lecture, name='edit_lecture'),
    path('delete-lecture/<int:lecture_id>/', views.delete_lecture, name='delete_lecture'),
    path('delete-revision/<int:revision_id>/', views.delete_revision, name='delete_revision'),
    path('mark-done/<int:revision_id>/', views.mark_revision_done, name='mark_done'),
    path('reschedule/<int:revision_id>/', views.reschedule_revision, name='reschedule'),
]