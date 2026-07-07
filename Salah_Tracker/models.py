from django.db import models
from django.contrib.auth.models import User
from core.models import SoftDeleteModel

# -----------------
# Permanent Templates
# -----------------

class Fard(SoftDeleteModel):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fard_prayers')

    def __str__(self):
        return self.name


class Sunnah(SoftDeleteModel):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sunnah_prayers')
    fard = models.ForeignKey(Fard, on_delete=models.CASCADE, related_name='linked_sunnah')

    def __str__(self):
        return f"{self.name} (linked to {self.fard.name})"


class PrayerTime(SoftDeleteModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='prayer_times')
    fajr = models.TimeField()
    dhuhr = models.TimeField()
    asr = models.TimeField()
    maghrib = models.TimeField()
    isha = models.TimeField()

    def __str__(self):
        return f"Prayer times for {self.user.username}"


# -----------------
# Daily Records
# -----------------

class DailyFard(SoftDeleteModel):
    fard = models.ForeignKey(Fard, on_delete=models.CASCADE, related_name='daily_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    completed = models.BooleanField(default=False)
    completed_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.fard.name} on {self.date}"


class DailySunnah(SoftDeleteModel):
    sunnah = models.ForeignKey(Sunnah, on_delete=models.CASCADE, related_name='daily_records')
    daily_fard = models.ForeignKey(DailyFard, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    completed = models.BooleanField(default=False)
    completed_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sunnah.name} on {self.date}"


class Nafl(SoftDeleteModel):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nafl_prayers')
    time = models.DateTimeField()

    def __str__(self):
        return self.name


class Dua(SoftDeleteModel):
    name = models.CharField(max_length=50)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duas')

    def __str__(self):
        return self.name


class QuranReading(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quran_readings')
    date = models.DateField(auto_now_add=True)
    surah = models.CharField(max_length=100)
    start_ayah = models.PositiveIntegerField()
    end_ayah = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.surah} ({self.start_ayah}-{self.end_ayah}) on {self.date}"


class Azkaar(SoftDeleteModel):
    PRAYER_CHOICES = [
        ("Subhanallah", "Subhanallah"),
        ("AlHamdulillah", "AlHamdulillah"),
        ("Allahu Akbar", "Allahu Akbar"),
        ("Astaghfirullah", "Astaghfirullah"),
        ("Subhanallahi w bihamdihi", "Subhanallahi w bihamdihi"),
        ("Lailahaillallah", "Lailahaillallah"),
        ("Other", "Other"),
    ]
    name = models.CharField(max_length=50, choices=PRAYER_CHOICES)
    count = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='azkaar')
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name