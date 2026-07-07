from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('todo/', include('todo.urls')),
    path('notes/', include('notes.urls')),
    path('time/', include('daily.urls')),
    path('test/', include('test_app.urls')),
    path('password/', include('password.urls')),
    path('data/', include('habit.urls')),
    path('diary/', include('diary.urls')),
    path('logs/', include('logs.urls')),
    path('salah/', include('Salah_Tracker.urls')),
    path('omr/', views.omr),

    path('login', views.loginUser),
    path('logout', views.logoutUser),
    path('forgot_password', views.forgetPass),
    path('signup', views.createac),
    path('profile', views.user_profile, name='profile'),
    path('help-center', views.help_center, name='help_center'),
    path('privacy-policy', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service', views.terms_of_service, name='terms_of_service'),
    path('revision/', include('revision.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
