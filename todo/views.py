from django.shortcuts import render, redirect, get_object_or_404
from .models import Todo, Syllabus
from revision.models import Subject
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
import json
from django.utils import timezone

@login_required
def task_list(request):
    tasks = Todo.objects.filter(user=request.user).order_by('due')
    return render(request, 'todo/task_list.html', {'tasks': tasks})

@login_required
def task_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        due = request.POST.get('date') or timezone.now()
        task = Todo(title=title, due=due, user=request.user)
        task.save()
        return redirect('task_list')
    return render(request, 'todo/task_form.html')

@login_required
def task_update(request, pk):
    task = get_object_or_404(Todo, pk=pk, user=request.user)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.completed = request.POST.get('completed') == 'on'
        due_date = request.POST.get('date')
        if due_date:
            task.due = due_date
        task.save()
        return redirect('task_list')
    return render(request, 'todo/task_form.html', {'task': task})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Todo, pk=pk, user=request.user)
    task.delete()
    return redirect('task_list')

@login_required
def syal_delete(request, id):
    syal = get_object_or_404(Syllabus, id=id, user=request.user)
    syal.delete()
    return redirect('/todo/syllabus')

@login_required
def syal_add(request):
    if request.method == 'POST':
        subject_id = request.POST.get('Subject')
        custom_subject_name = request.POST.get('custom_subject')
        chapter = request.POST.get('Chapter')
        
        subject = None
        if subject_id == 'new' and custom_subject_name:
            subject, created = Subject.objects.get_or_create(
                name=custom_subject_name.strip().title(),
                user=request.user,
                defaults={'normalized_name': custom_subject_name.strip().lower()}
            )
        elif subject_id and subject_id != 'new':
            subject = get_object_or_404(Subject, id=subject_id, user=request.user)
            
        if subject and chapter:
            Syllabus.objects.create(subject=subject, chapter=chapter, normalized_chapter=chapter.lower(), user=request.user)
        return redirect('/todo/syllabus')
    subjects = Subject.objects.filter(user=request.user)
    return render(request, 'todo/syllabus_add.html', {'subjects': subjects})

@login_required
def syal_update(request, id):
    syal = get_object_or_404(Syllabus, id=id, user=request.user)
    if request.method == 'POST':
        syal.chapter = request.POST.get('Chapter', syal.chapter)
        syal.normalized_chapter = syal.chapter.lower()
        subject_id = request.POST.get('Subject')
        if subject_id:
            syal.subject = get_object_or_404(Subject, id=subject_id, user=request.user)
        
        syal.lecture = request.POST.get('Lecture') == 'on'
        syal.notes = request.POST.get('Notes') == 'on'
        syal.ncert = request.POST.get('NCERT') == 'on'
        syal.dpp = request.POST.get('DPP') == 'on'
        syal.punch = request.POST.get('Punch') == 'on'
        syal.revision = request.POST.get('Revision') == 'on'
        syal.done = request.POST.get('Done') == 'on'

        # Auto complete logic
        if syal.lecture and syal.notes and syal.ncert and syal.dpp and syal.punch and syal.revision and syal.done:
            syal.completed = True
        else:
            syal.completed = False

        syal.save()
        messages.success(request, 'Syllabus updated successfully!')
        return redirect('/todo/syllabus')

    subjects = Subject.objects.filter(user=request.user)
    return render(request, 'todo/syllabus_update.html', {'syal': syal, 'subjects': subjects})

@login_required
def syalfun(request):
    per_subject = (
        Syllabus.objects
        .filter(user=request.user)
        .values('subject__name')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(completed=True))
        )
    )

    labels = [entry['subject__name'] for entry in per_subject]
    totals_list = [entry['total'] for entry in per_subject]
    completeds_list = [entry['completed'] for entry in per_subject]

    labels_json = mark_safe(json.dumps(labels))
    totals_json = mark_safe(json.dumps(totals_list))
    completeds_json = mark_safe(json.dumps(completeds_list))

    completed_count = Syllabus.objects.filter(user=request.user, completed=True).count()
    tc = Syllabus.objects.filter(user=request.user).count()
    data = Syllabus.objects.filter(user=request.user).select_related('subject')
    subjects = Subject.objects.filter(user=request.user)
    
    # Check if user has Premium+ (₹99 or above)
    is_premium_plus = (
        hasattr(request.user, 'subscription') and 
        request.user.subscription.is_valid() and 
        request.user.subscription.plan and 
        request.user.subscription.plan.price >= 99
    )
    
    from .models import SyllabusPreset
    presets = SyllabusPreset.objects.all()

    context = {
        'data': data,
        'tc': tc,
        'completed_count': completed_count,
        'labels_json': labels_json,
        'totals_json': totals_json,
        'completeds_json': completeds_json,
        'subjects': subjects,
        'is_premium_plus': is_premium_plus,
        'presets': presets,
    }
    return render(request, 'todo/syllabus.html', context)


import csv
import io
import os
import urllib.request
from .models import SyllabusPreset

@login_required
def import_syllabus_preset(request):
    if request.method == 'POST':
        preset_id = request.POST.get('preset_id')
        
        is_premium_plus = (
            hasattr(request.user, 'subscription') and 
            request.user.subscription.is_valid() and 
            request.user.subscription.plan and 
            request.user.subscription.plan.price >= 99
        )
        
        if not is_premium_plus:
            messages.error(request, 'Importing pre-built syllabus templates is exclusively for Premium+ (₹99/mo or above) subscribers.')
            return redirect('/todo/syllabus/')
            
        preset = get_object_or_404(SyllabusPreset, id=preset_id)
        csv_text = None
        
        if preset.csv_file:
            try:
                preset.csv_file.open('r')
                csv_text = preset.csv_file.read()
                if isinstance(csv_text, bytes):
                    csv_text = csv_text.decode('utf-8-sig')
                preset.csv_file.close()
            except Exception as e:
                csv_text = None
                
        if not csv_text and preset.csv_link:
            link = preset.csv_link.strip()
            if os.path.exists(link):
                try:
                    with open(link, 'r', encoding='utf-8-sig') as f:
                        csv_text = f.read()
                except Exception as e:
                    csv_text = None
            elif link.startswith('http://') or link.startswith('https://'):
                try:
                    req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as resp:
                        csv_text = resp.read().decode('utf-8-sig')
                except Exception as e:
                    csv_text = None

        if not csv_text:
            messages.error(request, 'Could not read CSV file for this syllabus preset.')
            return redirect('/todo/syllabus/')

        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            imported_count = 0
            for row in reader:
                chapter_name = row.get('Chapter', '').strip()
                subject_name = row.get('Subject', '').strip()
                
                if chapter_name and subject_name:
                    subj_obj, _ = Subject.objects.get_or_create(
                        user=request.user,
                        name=subject_name.title(),
                        defaults={'normalized_name': subject_name.lower()}
                    )
                    
                    syll_obj, created = Syllabus.objects.get_or_create(
                        user=request.user,
                        subject=subj_obj,
                        chapter=chapter_name,
                        defaults={'normalized_chapter': chapter_name.lower()}
                    )
                    if created:
                        imported_count += 1
                        
            messages.success(request, f'Successfully imported {imported_count} chapters from "{preset.title}"!')
        except Exception as e:
            messages.error(request, f'Error parsing syllabus CSV file: {str(e)}')
            
    return redirect('/todo/syllabus/')



from django.http import JsonResponse

@login_required
def task_toggle(request, pk):
    task = get_object_or_404(Todo, pk=pk, user=request.user)
    task.completed = not task.completed
    task.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
        return JsonResponse({'status': 'success', 'completed': task.completed})
    return redirect('task_list')
