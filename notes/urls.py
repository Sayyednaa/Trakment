from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.note_upload, name='upload'),
    path('view/<int:note_id>/', views.view_notes, name='view_notes'),
    path('delete/<int:note_id>/', views.delete_note, name='delete'),
]