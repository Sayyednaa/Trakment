from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

class data(SoftDeleteModel):
    name = models.CharField(max_length=100)
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_good_habit = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Habit(SoftDeleteModel):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_good_habit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class HabitEntry(SoftDeleteModel):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField()

    def __str__(self):
        return f"{self.habit.name} on {self.date}"
