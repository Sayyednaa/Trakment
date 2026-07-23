import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Avg
from django.utils.timezone import now, make_aware
from django.db.models.functions import TruncMonth, TruncDay, ExtractWeek, ExtractYear
from .models import Time
from revision.models import Subject
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required

@login_required
def monthly_summary(request):
    monthly_summaries = Time.objects.filter(user=request.user).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_duration=Sum('duration'),
        avg_duration=Avg('duration')
    ).order_by('month')
    return monthly_summaries

@login_required
def home(request):
    today_date = now().date()

    try:
        time_entries = Time.objects.filter(user=request.user).order_by('-date')
        result = time_entries.aggregate(Sum('duration'), Avg('duration'))
        tDays = time_entries.values('date__date').distinct().count()
        zeroDay = Time.objects.filter(duration=0, user=request.user).count()

        duration = result['duration__sum'] or 0
        average = result['duration__avg'] or 0
        months = monthly_summary(request)

        day_with_highest_duration = Time.objects.filter(user=request.user).annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            total_duration=Sum('duration')
        ).order_by('-total_duration').first()

        HighestDay = f"{day_with_highest_duration['day'].date()} : {day_with_highest_duration['total_duration']}" if day_with_highest_duration else None

        week_with_highest_duration = Time.objects.filter(user=request.user).annotate(
            week=ExtractWeek('date'),
            year=ExtractYear('date')
        ).values('year', 'week').annotate(
            total_duration=Sum('duration')
        ).order_by('-total_duration').first()

        week = None
        if week_with_highest_duration:
            year = week_with_highest_duration['year']
            week_number = week_with_highest_duration['week']
            start_of_week = datetime.strptime(f"{year}-W{week_number}-1", "%G-W%V-%u").date()
            end_of_week = start_of_week + timedelta(days=6)
            total_duration_of_highest_week = Time.objects.filter(
                user=request.user,
                date__range=[start_of_week, end_of_week]
            ).aggregate(total_duration=Sum('duration'))['total_duration'] or 0
            week = f"{start_of_week} to {end_of_week} : {total_duration_of_highest_week}"

        subjects = Subject.objects.filter(user=request.user)

        # Calculate time spent per subject
        subject_times = Time.objects.filter(user=request.user, subject__isnull=False).values('subject__name').annotate(
            total_duration=Sum('duration')
        ).order_by('-total_duration')
        
        subject_names = [item['subject__name'] for item in subject_times]
        subject_durations = [float(item['total_duration']) for item in subject_times]

        return render(
            request,
            'daily/index.html',
            {
                'time_entries': time_entries,
                'hours': duration,
                'avg': average,
                'zero': zeroDay,
                'tday': tDays,
                'month': months,
                'highday': HighestDay,
                'week': week,
                'subjects': subjects,
                'subject_names_json': json.dumps(subject_names),
                'subject_durations_json': json.dumps(subject_durations),
            }
        )
    except Exception as e:
        return render(
            request,
            'daily/index.html',
            {
                'error': str(e),
                'subjects': Subject.objects.filter(user=request.user)
            }
        )

@login_required
def add(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        duration = request.POST.get('duration', 0)
        subject_id = request.POST.get('subject')
        
        if date_str:
            date_obj = make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        else:
            date_obj = now()
            
        subject = get_object_or_404(Subject, id=subject_id, user=request.user) if subject_id else None
            
        if subject:
            Time.objects.create(
                date=date_obj,
                duration=int(duration),
                subject=subject,
                user=request.user
            )
            
        return redirect('/time/')
        
    subjects = Subject.objects.filter(user=request.user)
    return render(request, 'daily/add.html', {'subjects': subjects})

@login_required
def delete(request, id):
    entry = get_object_or_404(Time, id=id, user=request.user)
    entry.delete()
    return redirect('/time/')


@login_required
def update(request, id):
    entry = get_object_or_404(Time, id=id, user=request.user)
    if request.method == 'POST':
        date_str = request.POST.get('date')
        duration = request.POST.get('duration', 0)
        subject_id = request.POST.get('subject')
        
        if date_str:
            entry.date = make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        entry.duration = float(duration) if duration else 0.0
        
        if subject_id:
            entry.subject = get_object_or_404(Subject, id=subject_id, user=request.user)
        else:
            entry.subject = None
            
        entry.save()
        return redirect('/time/')
        
    subjects = Subject.objects.filter(user=request.user)
    return render(request, 'daily/update.html', {'entry': entry, 'subjects': subjects})
