from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

class Password(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passwords')
    platform = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    pass_hash = models.CharField(max_length=255)  # 'pass' is a reserved keyword in python
    iv = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.platform

    @property
    def website(self):
        return self.platform

    @website.setter
    def website(self, value):
        self.platform = value

    @property
    def password(self):
        return self.pass_hash

    @password.setter
    def password(self, value):
        self.pass_hash = value