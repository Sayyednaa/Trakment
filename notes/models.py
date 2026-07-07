from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

class Note(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    tags = models.CharField(max_length=255, null=True, blank=True)

    @property
    def tag_list(self):
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []

    def __str__(self):
        return f"Note by {self.user.username}"
