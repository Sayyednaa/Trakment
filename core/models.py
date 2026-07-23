from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # By default, only return objects that haven't been deleted
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_with_deleted(self):
        # Return all objects including deleted ones
        return super().get_queryset()

    def deleted(self):
        # Return only deleted objects
        return super().get_queryset().filter(deleted_at__isnull=False)

class SoftDeleteModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """Soft delete the record"""
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, *args, **kwargs):
        """Actually remove the record from the database"""
        super().delete(*args, **kwargs)

    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        self.save()


class AppSettings(SoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='app_settings')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    username_override = models.CharField(max_length=255, null=True, blank=True, unique=True)
    study_target = models.IntegerField(null=True, blank=True)
    target = models.DateTimeField(null=True, blank=True)
    notification = models.BooleanField(default=True)

    def __str__(self):
        return f"Settings for {self.user.username}"
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    target_date = models.DateField(default=date(2026, 4, 3))
    target_study_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def has_unread_messages(self):
        from .models import Message
        return Message.objects.filter(receiver=self.user, is_read=False).exists()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.content[:20]}"
