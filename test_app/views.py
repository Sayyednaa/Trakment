from django.http import JsonResponse
from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import datetime
from .models import Test, TestData, SelfTest
from todo.models import Syllabus
from revision.models import Subject

@login_required
def home(request):
    tests = Test.objects.filter(user=request.user).order_by('test_date')
    subjects = Subject.objects.filter(user=request.user)
    
    # 1. all_data (pivoted marks per test for the table)
    all_data = []
    for test in tests:
        entry = {
            'id': test.id,
            'date': test.test_date,
        }
        for sub in subjects:
            entry[sub.name] = None
        
        test_marks = TestData.objects.filter(test=test)
        for mark in test_marks:
            entry[mark.subject.name] = mark.marks
            
        entry['marks_list'] = [entry[sub.name] for sub in subjects]
        
        data_attrs = ""
        for sub in subjects:
            val = entry[sub.name]
            val_str = str(val) if val is not None else ""
            data_attrs += f' data-mark-{sub.name}="{val_str}"'
        entry['data_attributes'] = data_attrs
        
        all_data.append(entry)

    # 2. total_marks_by_date (for the bar chart)
    total_marks_by_date = []
    for test in tests:
        total = TestData.objects.filter(test=test).aggregate(total_marks=Sum('marks'))['total_marks'] or 0
        date_str = test.test_date.strftime('%Y-%m-%d') if test.test_date else '-'
        total_marks_by_date.append({
            'date': date_str,
            'total_marks': total
        })

    # 3. Subject-wise marks list (for line charts)
    def get_subject_marks(subject_name):
        data_points = []
        for test in tests:
            mark_obj = TestData.objects.filter(test=test, subject__name__iexact=subject_name).first()
            if mark_obj:
                date_str = test.test_date.strftime('%Y-%m-%d') if test.test_date else '-'
                data_points.append((date_str, mark_obj.marks))
        return data_points

    botany_marks = get_subject_marks('Botany')
    zoology_marks = get_subject_marks('Zoology')
    inorganic_marks = get_subject_marks('Inorganic')
    physical_marks = get_subject_marks('Physical')
    organic_marks = get_subject_marks('Organic')
    physics_marks = get_subject_marks('Physics')

    context = {
        'all_data': all_data,
        'total_marks_by_date': total_marks_by_date,
        'botany_marks': botany_marks,
        'zoology_marks': zoology_marks,
        'inorganic_marks': inorganic_marks,
        'physical_marks': physical_marks,
        'organic_marks': organic_marks,
        'physics_marks': physics_marks,
        'subjects': subjects,
    }
    return render(request, 'test/index.html', context)

@login_required
def add(request):
    subjects = Subject.objects.filter(user=request.user)
    if request.method == 'POST':
        test_date_str = request.POST.get('date')
        test_name = request.POST.get('name', 'General Test')
        if test_date_str:
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
        else:
            test_date = datetime.now()
            
        test = Test(user=request.user, name=test_name, test_date=test_date)
        test.save()

        # Add marks for each subject selected
        for subject in subjects:
            marks = request.POST.get(f'subject_{subject.id}')
            if marks:
                TestData.objects.create(
                    user=request.user,
                    test=test,
                    subject=subject,
                    marks=float(marks)
                )

        messages.success(request, "Test data added successfully!")
        return redirect('test:home')

    return render(request, 'test/add.html', {'subjects': subjects})

@login_required
def delete(request, id):
    test = get_object_or_404(Test, id=id, user=request.user)
    test.delete()
    return redirect('test:home')

@login_required
def update(request, id):
    test = get_object_or_404(Test, id=id, user=request.user)
    subjects = Subject.objects.filter(user=request.user)
    
    if request.method == 'POST':
        test_date_str = request.POST.get('date')
        if test_date_str:
            test.test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
        test.save()

        # Update or create marks
        for subject in subjects:
            marks = request.POST.get(f'subject_{subject.id}')
            if marks:
                td_obj, created = TestData.objects.get_or_create(
                    user=request.user,
                    test=test,
                    subject=subject,
                    defaults={'marks': float(marks)}
                )
                if not created:
                    td_obj.marks = float(marks)
                    td_obj.save()
            else:
                # If blank, delete it
                TestData.objects.filter(test=test, subject=subject).delete()
                
        messages.success(request, "Test data updated successfully!")
        return redirect('test:home')

    # Prep initial data for form
    data = {}
    test_data = TestData.objects.filter(test=test)
    for mark in test_data:
        data[mark.subject.name] = mark.marks
    data['id'] = test.id
    
    date_str = test.test_date.strftime('%Y-%m-%d') if test.test_date else ''
    return render(request, 'test/update.html', {'data': data, 'subjects': subjects, 'date': date_str, 'test': test})

@login_required
def self_test(request):
    if request.method == 'POST':
        chapter_val = request.POST.get('chapter_id') or request.POST.get('chapter')
        if chapter_val and str(chapter_val).isdigit():
            chapter = get_object_or_404(Syllabus, id=int(chapter_val), user=request.user)
        else:
            chapter = get_object_or_404(Syllabus, Cname=chapter_val, user=request.user)
            
        questions = int(request.POST.get('questions', 0))
        attempted = int(request.POST.get('attempted', 0))
        correct = int(request.POST.get('correct', 0))
        incorrect = int(request.POST.get('incorrect', 0))
        time = request.POST.get('time')
        
        plus_marks = correct * 4
        minus_marks = incorrect * 1
        total_marks = plus_marks - minus_marks
        max_marks = questions * 4
        percentage = (total_marks / max_marks) * 100 if max_marks > 0 else 0
        
        time_seconds = 0
        if time:
            if ':' in str(time):
                try:
                    parts = str(time).split(':')
                    if len(parts) == 3:
                        time_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        time_seconds = int(parts[0]) * 60 + int(parts[1])
                except ValueError:
                    time_seconds = 0
            else:
                try:
                    time_seconds = int(time)
                except ValueError:
                    time_seconds = 0

        st = SelfTest(
            user=request.user,
            chapter=chapter,
            questions=questions,
            attempted=attempted,
            correct=correct,
            incorrect=incorrect,
            plus_marks=plus_marks,
            minus_marks=minus_marks,
            total_marks=total_marks,
            percentage=percentage,
            time=time_seconds,
            date_taken=datetime.now()
        )
        st.save()
        
        # Auto-update chapter's test stats
        chapter.update_test_stats()
        
        # Handle AJAX/fetch request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json' or 'chapter_id' in request.POST:
            return JsonResponse({'status': 'success', 'message': 'Self test recorded successfully!'})
            
        messages.success(request, "Self test recorded successfully!")
        return redirect('test:self_test_analysis')

    chapters = Syllabus.objects.filter(user=request.user)
    return render(request, 'test/self_test.html', {'chapters': chapters})

@login_required
def self_test_analysis(request):
    tests = SelfTest.objects.filter(user=request.user).order_by('-date_taken')
    return render(request, 'test/list_self_tests.html', {'self_tests': tests, 'tests': tests})

@login_required
def delete_self_test(request, id):
    test = get_object_or_404(SelfTest, id=id, user=request.user)
    test.delete()
    return redirect('test:self_test_analysis')

@login_required
def chapter_analytics(request, chapter_id):
    import json
    chapter = get_object_or_404(Syllabus, id=chapter_id, user=request.user)
    tests = SelfTest.objects.filter(chapter=chapter, user=request.user).order_by('date_taken')
    
    total_tests = tests.count()
    avg_accuracy = 0
    best_score = 0
    avg_time_per_question = 0
    improvement = 0
    
    annotated_tests = []
    for i, test in enumerate(tests):
        test.attempt_number = i + 1
        time_seconds = test.time or 0
        minutes = time_seconds // 60
        seconds = time_seconds % 60
        test.time_taken = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        annotated_tests.append(test)
        
    if total_tests > 0:
        avg_accuracy = tests.aggregate(Avg('percentage'))['percentage__avg'] or 0
        best_score = tests.order_by('-percentage').first().percentage or 0
        
        total_questions = sum(t.questions for t in tests)
        total_time = sum(t.time for t in tests)
        avg_time_per_question = total_time / total_questions if total_questions > 0 else 0
        
        if total_tests > 1:
            first_pct = tests.first().percentage or 0
            last_pct = tests.last().percentage or 0
            improvement = last_pct - first_pct
            
    stats = {
        'total_tests': total_tests,
        'avg_accuracy': avg_accuracy,
        'best_score': best_score,
        'avg_time_per_question': avg_time_per_question
    }
    
    labels = [f"Attempt #{i+1}" for i in range(total_tests)]
    scores = [float(t.percentage) for t in tests]
    correct = [t.correct for t in tests]
    incorrect = [t.incorrect for t in tests]
    
    chart_data = {
        'labels': labels,
        'scores': scores,
        'correct': correct,
        'incorrect': incorrect
    }
    
    context = {
        'chapter': chapter,
        'tests': reversed(annotated_tests),
        'stats': stats,
        'improvement': improvement,
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'test/chapter_analytics.html', context)


@login_required
def self_tests_statistics(request):
    tests = SelfTest.objects.filter(user=request.user).order_by('date_taken')
    
    if not tests.exists():
        return JsonResponse({'error': 'No test data available'})
        
    dates = [t.date_taken.strftime('%Y-%m-%d') for t in tests]
    percentages = [float(t.percentage) for t in tests]
    
    chapter_stats_dict = {}
    for t in tests:
        cname = t.chapter.Cname
        if cname not in chapter_stats_dict:
            chapter_stats_dict[cname] = []
        chapter_stats_dict[cname].append(t.percentage)
        
    chapter_stats = []
    for cname, pcts in chapter_stats_dict.items():
        chapter_stats.append({
            'chapter_name': cname,
            'avg_accuracy': sum(pcts) / len(pcts) if pcts else 0
        })
        
    return JsonResponse({
        'time_series': {
            'dates': dates,
            'percentages': percentages
        },
        'chapter_stats': chapter_stats
    })


@login_required
def self_test_detail(request, id):
    self_test = get_object_or_404(SelfTest, id=id, user=request.user)
    accuracy = (self_test.correct / self_test.attempted * 100) if self_test.attempted > 0 else 0
    efficiency = (self_test.attempted / self_test.questions * 100) if self_test.questions > 0 else 0
    
    time_seconds = self_test.time or 0
    minutes = time_seconds // 60
    seconds = time_seconds % 60
    time_display = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    
    context = {
        'self_test': self_test,
        'accuracy': round(accuracy, 1),
        'efficiency': round(efficiency, 1),
        'time_display': time_display
    }
    return render(request, 'test/self_test_detail.html', context)
