from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel
from revision.models import Subject

class Time(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    duration = models.IntegerField()  # duration in minutes/hours? The schema says integer, I will assume minutes, but in old DB it was Decimal. I'll use Integer based on db.txt
    date = models.DateTimeField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    focus_session = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} - {self.duration}"
