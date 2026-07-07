"""
URL configuration for Salah project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Salah_Tracker import views, api
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

    path("", views.home, name="Home"),
    path("add-nafl/", views.add_nafl, name="add_nafl"),
    path("add-quran/", views.add_quran_reading, name="add_quran"),
    path("stats/", views.stats, name="stats"),
    path("add-azkaar/", views.add_azkaar, name="add_azkaar"),
    path("add-prayer-time/", views.prayer_times, name="add_prayer_time"),
    path("profile/", views.profile, name="profile"),
    path("toggle-fard/", views.toggle_fard, name="toggle_fard"),
    path("toggle-sunnah/", views.toggle_sunnah, name="toggle_sunnah"),
    path('prayer-stats/', views.prayer_detail_stats, name='prayer_detail_stats'),
    path('quran-stats/', views.quran_stats_view, name='quran_stats_view'),
    path('azkaar-stats/', views.azkaar_stats_view, name='azkaar_stats_view'),
    path('nafl-stats/', views.nafl_stats_view, name='nafl_stats_view'),
     path('api/prayer-times/', views.prayer_times_api, name='prayer-times-api'),
     
     # Mobile App APIs
     path('api/daily-prayers/', api.daily_prayers_api, name='api_daily_prayers'),
     path('api/toggle-fard/', api.toggle_fard_api, name='api_toggle_fard'),
     path('api/toggle-sunnah/', api.toggle_sunnah_api, name='api_toggle_sunnah'),
     path('api/add-azkaar/', api.add_azkaar_api, name='api_add_azkaar'),
     path('api/add-quran/', api.add_quran_api, name='api_add_quran'),
     path('api/add-nafl/', api.add_nafl_api, name='api_add_nafl'),
     path('api/stats/', api.get_stats_api, name='api_stats'),
     path('api/next-prayer/', api.get_next_prayer_api, name='api_next_prayer'),
     path('api/docs/', views.api_docs, name='api_docs'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)