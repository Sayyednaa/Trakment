from datetime import timedelta
from .models import Revision, Lecture

def schedule_revision(lecture,request):
    revision_dates = [
        lecture.date_added,                   # Same day
        lecture.date_added + timedelta(days=2),  # After 2 days
        lecture.date_added + timedelta(days=6),  # After 6 days
        lecture.date_added + timedelta(days=15), # After 15 days
        lecture.date_added + timedelta(days=30), # After 30 days
    ]
    for date in revision_dates:
        Revision.objects.create(lecture=lecture, revision_date=date,user=request.user)