from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

class Subject(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class RevisionLecture(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    date = models.DateTimeField()
    revision_plan = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.subject.name} - {self.topic}"

class Revision(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lecture = models.ForeignKey(RevisionLecture, on_delete=models.CASCADE)
    date = models.DateTimeField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Revise {self.lecture.topic} on {self.date}"