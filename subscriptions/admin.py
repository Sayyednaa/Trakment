from django.contrib import admin
from .models import Plan, UserSubscription, Payment

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')
    search_fields = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active', 'is_valid')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username', 'user__email')
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'utr_id', 'status', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'utr_id')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['approve_payments', 'reject_payments']

    def approve_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'approved'
            payment.save()
        self.message_user(request, f"{queryset.count()} payments approved.")
    approve_payments.short_description = "Approve selected payments"

    def reject_payments(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} payments rejected.")
    reject_payments.short_description = "Reject selected payments"
