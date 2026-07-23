from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, UserSubscription

@receiver(post_save, sender=Payment)
def handle_payment_approval(sender, instance, **kwargs):
    if instance.status == 'approved':
        # Create or update the user's subscription
        sub, created = UserSubscription.objects.get_or_create(
            user=instance.user,
            defaults={
                'plan': instance.plan,
                'end_date': timezone.now() + timezone.timedelta(days=instance.plan.duration_days),
                'is_active': True
            }
        )
        if not created:
            # If they already have a subscription, update it
            # If it's still active, we add to the end_date. Otherwise, start from today.
            if sub.is_valid():
                sub.end_date = sub.end_date + timezone.timedelta(days=instance.plan.duration_days)
            else:
                sub.end_date = timezone.now() + timezone.timedelta(days=instance.plan.duration_days)
            sub.plan = instance.plan
            sub.is_active = True
            sub.save()
