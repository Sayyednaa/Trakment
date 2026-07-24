from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel
from revision.models import Subject

class Syllabus(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    chapter = models.CharField(max_length=255)
    normalized_chapter = models.CharField(max_length=255)
    dpp = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    lecture = models.BooleanField(default=False)
    ncert = models.BooleanField(default=False)
    notes = models.BooleanField(default=False)
    punch = models.BooleanField(default=False)
    revision = models.BooleanField(default=False)
    test = models.FloatField(null=True, blank=True)
    average_accuracy = models.FloatField(null=True, blank=True)
    best_score = models.IntegerField(null=True, blank=True)
    last_test_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Syllabus"
        ordering = ['subject', 'chapter']

    def __str__(self):
        return f"{self.subject.name} - {self.chapter}"

    @property
    def Cname(self):
        return self.chapter

    @Cname.setter
    def Cname(self, value):
        self.chapter = value

    @property
    def Subject(self):
        return self.subject.name

    def update_test_stats(self):
        """Update statistics based on all tests for this chapter"""
        from test_app.models import SelfTest

        tests = SelfTest.objects.filter(chapter=self, user=self.user)

        if tests.exists():
            self.test = float(tests.count())
            self.last_test_date = tests.latest('date_taken').date_taken
            self.best_score = int(tests.order_by('-percentage').first().percentage)
            self.average_accuracy = tests.aggregate(models.Avg('percentage'))['percentage__avg']
            self.save()


class Todo(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    due = models.DateTimeField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class SyllabusPreset(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    csv_file = models.FileField(upload_to='syllabus_presets/', blank=True, null=True)
    csv_link = models.CharField(max_length=500, blank=True, null=True, help_text="Direct URL to CSV file if hosted externally")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Syllabus Preset"
        verbose_name_plural = "Syllabus Presets"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

