from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from datetime import timedelta, datetime

from todo.models import Todo, Syllabus
from daily.models import Time
from test_app.models import Test, TestData
from notes.models import Note
from revision.models import Revision, RevisionLecture, Subject

from Salah_Tracker.models import Fard, Sunnah, Nafl, QuranReading, Azkaar, PrayerTime, DailyFard, DailySunnah
from Salah_Tracker.helpers import create_daily_records, get_daily_fard_time, get_daily_sunnah_time

def calculate_study_time_change(user):
    today = timezone.now().date()

    current_start = today - timedelta(days=6)
    current_end = today

    previous_start = today - timedelta(days=13)
    previous_end = today - timedelta(days=7)

    current_entries = Time.objects.filter(
        user=user,
        date__date__gte=current_start,
        date__date__lte=current_end
    )
    current_total = current_entries.aggregate(total_duration=Sum('duration'))['total_duration'] or 0

    previous_entries = Time.objects.filter(
        user=user,
        date__date__gte=previous_start,
        date__date__lte=previous_end
    )
    previous_total = previous_entries.aggregate(total_duration=Sum('duration'))['total_duration'] or 0

    if previous_total == 0:
        if current_total == 0:
            percent_change = 0
        else:
            percent_change = 100
    else:
        percent_change = ((current_total - previous_total) / previous_total) * 100

    result = Time.objects.filter(user=user).aggregate(Avg('duration'))
    all_time_avg = result['duration__avg'] or 0

    return round(current_total, 2), round(percent_change, 2), round(all_time_avg, 2)

def home(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            name = request.POST.get('name')
            feedback = request.POST.get('msg')
            email = request.POST.get('email')
            role = request.POST.get('role')
            # Assign to target user or superuser since unauthenticated
            target_user = User.objects.first()
            if target_user:
                Note.objects.create(
                    content=f'From:{name}\n Role: {role}\nEmail: {email}\n Feedback:{feedback}',
                    user=target_user
                )
        return render(request, 'main/landing.html')

    user = request.user
    today_date = timezone.now().date()
    now_time = timezone.localtime()

    # Create daily records
    try:
        create_daily_records(user)
    except Exception as e:
        print(f"Error creating records: {e}")

    # Fetch stats
    current_total, percent_change, all_time_avg = calculate_study_time_change(user)
    
    today_start = timezone.make_aware(datetime.combine(today_date, datetime.min.time()))
    tomorrow_start = today_start + timedelta(days=1)
    
    tasks = Todo.objects.filter(user=user, completed=False, due__gte=today_start, due__lt=tomorrow_start).order_by('due')
    recent_notes = Note.objects.filter(user=user).order_by('-created_at')[:3]
    from test_app.models import TestData
    recent_tests = TestData.objects.filter(user=user).select_related('test').order_by('-test__test_date')[:3]
    time_entries = Time.objects.filter(user=user).order_by('-date')[:3]
    
    pending_revisions = Revision.objects.filter(user=user, completed=False, date__gte=today_start, date__lt=tomorrow_start).order_by('date')
    
    daily_fard = DailyFard.objects.filter(user=user, date=today_date).order_by("fard__name")
    fard_with_times = [(f, get_daily_fard_time(f)) for f in daily_fard]
    
    upcoming_prayer = None
    upcoming_prayer_time = None
    sorted_fard_with_times = sorted(fard_with_times, key=lambda x: x[1].time() if x[1] else datetime.max.time())
    
    for f, time_value in sorted_fard_with_times:
        if time_value and time_value.time() > now_time.time():
            upcoming_prayer = f
            upcoming_prayer_time = time_value
            break
            
    if not upcoming_prayer and sorted_fard_with_times:
        upcoming_prayer = sorted_fard_with_times[0][0]
        upcoming_prayer_time = sorted_fard_with_times[0][1]
        if upcoming_prayer_time:
            upcoming_prayer_time = upcoming_prayer_time + timedelta(days=1)

    # Calculate additional metrics for dashboard compatibility
    completedTask = Todo.objects.filter(user=user, completed=True).count()
    totalTask = Todo.objects.filter(user=user).count()
    
    from todo.models import Syllabus
    Tc = Syllabus.objects.filter(user=user).count()
    completedC = Syllabus.objects.filter(user=user, completed=True).count()
    
    from test_app.models import SelfTest
    
    # Test Charts & Avg Score
    last_self_tests = list(SelfTest.objects.filter(user=user).order_by('-date_taken')[:5])[::-1]
    if last_self_tests:
        test_dates = [t.date_taken.strftime('%b %d') for t in last_self_tests]
        test_percentages = [float(t.percentage) for t in last_self_tests]
        average_percentage = SelfTest.objects.filter(user=user).aggregate(Avg('percentage'))['percentage__avg'] or 0
    else:
        last_test_datas = list(TestData.objects.filter(user=user).select_related('test').order_by('-test__test_date')[:5])[::-1]
        test_dates = [t.test.test_date.strftime('%b %d') for t in last_test_datas if t.test and t.test.test_date]
        test_percentages = [float(t.marks) for t in last_test_datas]
        average_percentage = TestData.objects.filter(user=user).aggregate(Avg('marks'))['marks__avg'] or 0

    average_percentage = round(float(average_percentage), 1)
    
    # Study Chart (last 7 days)
    daily_durations = list(Time.objects.filter(user=user).order_by('-date')[:7])[::-1]

    # Fetch subjects for Focus Session
    subjects = Subject.objects.filter(user=user).order_by('name')

    context = {
        'is_authenticated': True,
        'user': user,
        'subjects': subjects,
        'tasks': tasks,
        'task': tasks,  # Singular for compatibility
        'recent_notes': recent_notes,
        'recent_tests': recent_tests,
        'time_entries': time_entries,
        'pending_revisions': pending_revisions,
        'revision_topics': pending_revisions,  # Compatibility for revision topics
        'current_total': current_total,
        'percent_change': percent_change,
        'change': percent_change,  # Compatibility for study time percentage change
        'total_study_time': current_total, # For dashboard weekly time
        'all_time_avg': all_time_avg,
        'upcoming_prayer': upcoming_prayer,
        'upcoming_prayer_time': upcoming_prayer_time,
        'fard_with_times': fard_with_times,  # Fix missing fard prayers on dashboard
        'completedTask': completedTask,
        'totalTask': totalTask,
        'Tc': Tc,
        'completedC': completedC,
        'average_percentage': average_percentage,
        'test_dates': test_dates,
        'test_percentages': test_percentages,
        'daily_durations': daily_durations,
    }

    return render(request, 'main/home.html', context)

def loginUser(request):
    if request.method == "POST":
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'main/login.html')

def logoutUser(request):
    logout(request)
    return redirect('/login')

def createac(request):
    if request.method == "POST":
        data = request.POST
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        user = User.objects.filter(username=username)
        if user.exists():
            messages.info(request, 'Username already taken')
            return redirect('/signup')

        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            email=email
        )
        user.save()
        messages.info(request, 'Account created successfully')
        return redirect('/login')
    return render(request, 'main/signup.html')

def forgetPass(request):
    return render(request, 'main/login.html') # fallback to login if not exists

@login_required
def user_profile(request):
    from test_app.models import SelfTest
    from daily.models import Time
    from todo.models import Todo
    from datetime import datetime
    
    user = request.user
    
    if request.method == "POST":
        # Check which form was submitted (Personal Info vs Study Goals)
        form_type = request.POST.get('form_type')
        
        if form_type == 'personal':
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()
            
            # Profile Photo
            if 'profile_photo' in request.FILES:
                user.userprofile.profile_photo = request.FILES['profile_photo']
                user.userprofile.save()
                
            messages.success(request, 'Personal Information updated successfully')
            
        elif form_type == 'goals':
            target_date_str = request.POST.get('target_date')
            target_hours_str = request.POST.get('target_study_hours')
            
            if target_date_str:
                user.userprofile.target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            if target_hours_str:
                user.userprofile.target_study_hours = target_hours_str
                
            user.userprofile.save()
            messages.success(request, 'Study Goals updated successfully')
            
        return redirect('/profile')
        
    # Calculate Metrics
    study_hrs = Time.objects.filter(user=user).aggregate(Sum('duration'))['duration__sum'] or 0
    tasks_done = Todo.objects.filter(user=user, completed=True).count()
    avg_score = SelfTest.objects.filter(user=user).aggregate(Avg('percentage'))['percentage__avg'] or 0
    avg_score = round(float(avg_score), 1)
    
    from .leaderboard_utils import calculate_user_points_all_time
    all_time_points = calculate_user_points_all_time(user)
    
    context = {
        'study_hrs': round(float(study_hrs), 1),
        'tasks_done': tasks_done,
        'avg_score': avg_score,
        'all_time_points': all_time_points,
    }
    
    return render(request, 'user/profile.html', context)


@csrf_exempt
@login_required
def omr(request):
    import json
    subjects_qs = Subject.objects.filter(user=request.user)
    subjects_list = [s.name for s in subjects_qs]
    
    chapters_dict = {}
    for s in subjects_qs:
        chapters = Syllabus.objects.filter(subject=s, user=request.user)
        chapters_dict[s.name] = [{'id': c.id, 'Cname': c.Cname} for c in chapters]
        
    context = {
        'subjects': subjects_list,
        'chapters_by_subject': json.dumps(chapters_dict)
    }
    return render(request, 'main/omr.html', context)


def help_center(request):
    return render(request, 'main/help_center.html')

def privacy_policy(request):
    return render(request, 'main/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'main/terms_of_service.html')

from .leaderboard_utils import get_global_leaderboard

@login_required
def leaderboard(request):
    rankings = get_global_leaderboard()
    return render(request, 'main/leaderboard.html', {'rankings': rankings})

@login_required
def public_profile(request, username):
    from django.shortcuts import get_object_or_404
    from .leaderboard_utils import calculate_user_points_all_time
    
    profile_user = get_object_or_404(User, username=username)
    all_time_points = calculate_user_points_all_time(profile_user)
    
    return render(request, 'user/public_profile.html', {
        'profile_user': profile_user,
        'all_time_points': all_time_points
    })

@login_required
def chat_inbox(request):
    from core.models import Message
    from django.db.models import Q, Max
    
    user = request.user
    
    # Get all messages where user is sender or receiver
    messages = Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-timestamp')
    
    # Get distinct conversational partners and the latest message
    conversations = {}
    for msg in messages:
        partner = msg.receiver if msg.sender == user else msg.sender
        if partner not in conversations:
            conversations[partner] = msg
            
    # Convert to list and sort by latest message timestamp
    inbox = [{'partner': p, 'latest_msg': m} for p, m in conversations.items()]
    inbox.sort(key=lambda x: x['latest_msg'].timestamp, reverse=True)
    
    return render(request, 'chat/inbox.html', {'inbox': inbox})

@login_required
def chat_thread(request, username):
    from django.shortcuts import get_object_or_404
    from core.models import Message
    from django.db.models import Q
    
    partner = get_object_or_404(User, username=username)
    user = request.user
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content and content.strip():
            Message.objects.create(sender=user, receiver=partner, content=content.strip())
            return redirect('chat_thread', username=username)
            
    # Mark messages as read
    Message.objects.filter(sender=partner, receiver=user, is_read=False).update(is_read=True)
    
    chat_msgs = Message.objects.filter(
        (Q(sender=user) & Q(receiver=partner)) | 
        (Q(sender=partner) & Q(receiver=user))
    ).order_by('timestamp')
    
    return render(request, 'chat/thread.html', {
        'partner': partner,
        'chat_messages': chat_msgs
    })
