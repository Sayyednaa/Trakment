from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import SoftDeleteModel
from revision.models import Subject

class LogEntry(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_logs')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField()

    class Meta:
        ordering = ['-start_time']
        verbose_name_plural = 'Log Entries'

    def __str__(self):
        return f"{self.start_time} - {self.end_time}: {self.description[:50]}"