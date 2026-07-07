from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

class data(SoftDeleteModel):
    name = models.CharField(max_length=100)
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name