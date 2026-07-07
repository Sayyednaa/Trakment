from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import RevisionLecture, Revision, Subject

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # New lectures added today (cast date to date)
    new_lectures = RevisionLecture.objects.filter(
        user=request.user,
        date__date=today
    )[:3]

    pending_revision = Revision.objects.filter(
        user=request.user,
        completed=False
    )
    
    pending_revision_today = Revision.objects.filter(
        user=request.user,
        completed=False,
        date__date=today
    )
    
    completed_revision_count = Revision.objects.filter(
        user=request.user,
        completed=True
    ).count()

    upcoming_revision_count = Revision.objects.filter(
        user=request.user,
        date__date__gt=today,
        completed=False
    ).count()
    
    overdue_revisions = Revision.objects.filter(
        user=request.user,
        date__date__lt=today,
        completed=False
    ).select_related('lecture').order_by('date')
    
    overdue_revision_count = overdue_revisions.count()

    subjects = Subject.objects.filter(user=request.user).order_by('name')

    return render(request, 'revision/home.html', {
        'new_lectures': new_lectures,
        'pending_revision': pending_revision,
        'completed_revision_count': completed_revision_count,
        'upcoming_revision_count': upcoming_revision_count,
        'pending_revision_today': pending_revision_today,
        'overdue_revisions': overdue_revisions,
        'overdue_revision_count': overdue_revision_count,
        'subjects': subjects,
    })

@login_required
def mark_revision_done(request, revision_id):
    revision = get_object_or_404(Revision, id=revision_id, user=request.user)
    revision.completed = True
    revision.save()
    return redirect('dashboard')

@login_required
def add_lecture(request):
    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        topic = request.POST.get('topic')

        if not subject_name or not topic:
            messages.error(request, "Both subject and topic are required")
            return redirect('dashboard')

        try:
            subject, created = Subject.objects.get_or_create(
                name=subject_name.strip().title(),
                user=request.user,
                defaults={'normalized_name': subject_name.strip().lower()}
            )

            revision_plan = request.POST.get('revision_plan', '1-3-7-14-30')
            
            # Map the selected plan to day offsets
            if revision_plan == '1-7-30':
                offsets = [1, 7, 30]
            elif revision_plan == '1-7-16-35':
                offsets = [1, 7, 16, 35]
            else:
                offsets = [1, 3, 7, 14, 30]
                revision_plan = '1-3-7-14-30' # Ensure default string

            now = timezone.now()
            new_lecture = RevisionLecture.objects.create(
                user=request.user,
                subject=subject,
                topic=topic,
                date=now,
                revision_plan=revision_plan
            )

            revision_dates = [now + timedelta(days=d) for d in offsets]
            for r_date in revision_dates:
                Revision.objects.create(
                    user=request.user,
                    lecture=new_lecture,
                    date=r_date,
                    completed=False
                )

            messages.success(request, f"Added '{topic}' to {subject.name}")
        except Exception as e:
            messages.error(request, f"Error: {e}")

        return redirect('dashboard')

@login_required
def delete_lecture(request, lecture_id):
    lecture = get_object_or_404(RevisionLecture, id=lecture_id, user=request.user)
    lecture.delete()
    messages.success(request, "Lecture and all associated revisions deleted successfully!")
    return redirect('dashboard')

@login_required
def delete_revision(request, revision_id):
    revision = get_object_or_404(Revision, id=revision_id, user=request.user)
    revision.delete()
    messages.success(request, "Revision task deleted successfully!")
    return redirect('dashboard')

@login_required
def reschedule_revision(request, revision_id):
    if request.method == 'POST':
        revision = get_object_or_404(Revision, id=revision_id, user=request.user)
        new_date_str = request.POST.get('new_date')
        if new_date_str:
            # We can parse standard date input string YYYY-MM-DD
            try:
                parsed_date = timezone.datetime.strptime(new_date_str, '%Y-%m-%d').date()
                revision.date = parsed_date
                revision.save()
                messages.success(request, "Revision rescheduled successfully!")
            except Exception as e:
                messages.error(request, f"Invalid date: {e}")
        else:
            messages.error(request, "Date is required")
    return redirect('dashboard')

@login_required
def edit_lecture(request, lecture_id):
    lecture = get_object_or_404(RevisionLecture, id=lecture_id, user=request.user)
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        topic = request.POST.get('topic')
        if subject_id:
            lecture.subject = get_object_or_404(Subject, id=subject_id, user=request.user)
        if topic:
            lecture.topic = topic
        lecture.save()
        messages.success(request, "Lecture updated successfully!")
    return redirect('dashboard')