from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel
from revision.models import Subject
from todo.models import Syllabus

class Test(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_date = models.DateTimeField()
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.name or 'Test'} on {self.test_date}"


class TestData(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks = models.FloatField()

    def __str__(self):
        return f"{self.subject.name}: {self.marks}"


class SelfTest(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Syllabus, on_delete=models.CASCADE)
    questions = models.IntegerField()
    attempted = models.IntegerField()
    correct = models.IntegerField()
    incorrect = models.IntegerField()
    plus_marks = models.IntegerField()
    minus_marks = models.IntegerField()
    total_marks = models.IntegerField()
    percentage = models.FloatField()
    date_taken = models.DateTimeField()
    time = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-date_taken']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.chapter:
            self.chapter.update_test_stats()

    def __str__(self):
        return f"{self.chapter.chapter} - {self.date_taken}"
