from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Plan(models.Model):
    PLAN_CHOICES = (
        ('free_trial', '1-Day Free Trial'),
        ('basic', 'Basic Plan (₹49/mo)'),
        ('premium', 'Premium+ (₹99/mo)'),
        ('yearly', 'Yearly All-Access (₹999/yr)'),
    )
    
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.IntegerField(help_text="Duration in days")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_name_display()

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and self.end_date >= timezone.now()

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    utr_id = models.CharField(max_length=100, unique=True, help_text="UPI Transaction ID (UTR)")
    screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.utr_id} ({self.status})"

class PaymentSettings(models.Model):
    upi_id = models.CharField(max_length=255, default="paytm.slax2x4@pty", help_text="The UPI ID to receive payments")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Setting"
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return "Global Payment Settings"
