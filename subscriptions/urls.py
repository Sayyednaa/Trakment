from django.urls import path
from . import views

urlpatterns = [
    # Business Dashboard
    path('dashboard/', views.business_overview, name='business_overview'),
    path('dashboard/users/', views.business_users, name='business_users'),
    path('dashboard/payments/', views.business_payments, name='business_payments'),
    path('dashboard/payments/<int:payment_id>/', views.business_payment_review, name='business_payment_review'),
    path('dashboard/syllabuses/', views.business_syllabuses, name='business_syllabuses'),
    path('dashboard/syllabuses/delete/<int:preset_id>/', views.business_syllabus_delete, name='business_syllabus_delete'),
    path('dashboard/plans/', views.business_plans, name='business_plans'),

    # Public Subscription Flow
    path('pricing/', views.pricing_view, name='pricing'),
    path('checkout/<int:plan_id>/', views.checkout_view, name='checkout'),
    path('status/', views.subscription_status, name='subscription_status'), # Kept for backward compatibility
]
