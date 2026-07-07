from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

class Diary(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
