from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from daily.models import Time
from todo.models import Todo, Syllabus
from revision.models import Revision
from test_app.models import TestData, SelfTest
from habit.models import data as HabitData
from collections import defaultdict
from django.db import models

def get_week_range():
    """Returns a timezone-aware (start_of_week, end_of_week) for the current week."""
    now = timezone.now()
    # Monday is 0, Sunday is 6
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)
    return start_of_week, end_of_week

def is_good_habit(name):
    """Simple heuristic for good vs bad habits based on name"""
    bad_keywords = ['quit', 'stop', 'no', 'bad', 'smoking', 'junk', 'sugar']
    name_lower = name.lower()
    for word in bad_keywords:
        if word in name_lower:
            return False
    return True

def calculate_habit_points(user, start_of_week, end_of_week):
    """
    Calculate habit points for the given week.
    Good Habits: 10 XP per day logged.
    Bad Habits: 10 XP per day NOT logged (gap day) during the week.
    """
    points = 0
    habits = HabitData.objects.filter(user=user)
    
    if not habits.exists():
        return 0

    habit_names = habits.values('name').distinct()
    
    week_dates = set()
    current_date = start_of_week.date()
    end_date = min(end_of_week.date(), timezone.now().date())
    
    while current_date <= end_date:
        week_dates.add(current_date)
        current_date += timedelta(days=1)
        
    for h in habit_names:
        habit_name = h['name']
        is_good = is_good_habit(habit_name)
        
        # Get dates this habit was logged in the current week
        logged_dates = set(habits.filter(
            name=habit_name,
            date__gte=start_of_week.date(),
            date__lte=end_date
        ).values_list('date', flat=True))
        
        if is_good:
            # 10 XP per day logged (streak day)
            points += len(logged_dates) * 10
        else:
            # Bad habit: 10 XP per gap day (day NOT logged)
            gap_days = len(week_dates) - len(logged_dates)
            points += gap_days * 10
            
    return points

def calculate_user_points_for_week(user, start_of_week, end_of_week):
    MAX_DAILY_XP = 1000
    MAX_WEEKLY_XP = 5000
    
    total_weekly_points = 0
    current_date = start_of_week
    
    while current_date < end_of_week:
        next_date = current_date + timedelta(days=1)
        daily_points = 0
        
        # 1. Study Time (Deep Focus Only)
        deep_focus_time = Time.objects.filter(
            user=user, 
            focus_session=True,
            date__gte=current_date, 
            date__lt=next_date
        ).aggregate(total_duration=models.Sum('duration'))['total_duration'] or 0
        
        daily_points += (deep_focus_time / 60.0) * 10
        
        # 2. Task Completion (Productivity)
        tasks = Todo.objects.filter(
            user=user, 
            completed=True,
            updated_at__gte=current_date,
            updated_at__lt=next_date
        )
        for task in tasks:
            daily_points += 10
            if task.due and task.updated_at.date() <= task.due.date():
                daily_points += 5

        # 3. Syllabus & Revision
        completed_chapters = Syllabus.objects.filter(
            user=user, 
            completed=True,
            updated_at__gte=current_date,
            updated_at__lt=next_date
        ).count()
        daily_points += completed_chapters * 50
        
        completed_revisions = Revision.objects.filter(
            user=user,
            completed=True,
            date__gte=current_date,
            date__lt=next_date
        ).count()
        daily_points += completed_revisions * 15

        # 4. Tests & Performance
        self_tests = SelfTest.objects.filter(
            user=user,
            date_taken__gte=current_date,
            date_taken__lt=next_date
        )
        for t in self_tests:
            daily_points += 20 + float(t.percentage)
            
        # Apply daily cap
        total_weekly_points += min(daily_points, MAX_DAILY_XP)
        
        current_date = next_date

    # 5. Habits (Habits are calculated weekly because of gap days)
    habit_points = calculate_habit_points(user, start_of_week, end_of_week)
    total_weekly_points += habit_points

    # Apply weekly cap
    return min(int(total_weekly_points), MAX_WEEKLY_XP)

def calculate_user_points_all_time(user):
    points = 0
    
    # 1. Study Time (Deep Focus Only)
    deep_focus_time = Time.objects.filter(
        user=user, 
        focus_session=True
    ).aggregate(total_duration=models.Sum('duration'))['total_duration'] or 0
    
    points += (deep_focus_time / 60.0) * 10
    
    # 2. Task Completion (Productivity)
    tasks = Todo.objects.filter(
        user=user, 
        completed=True
    )
    for task in tasks:
        points += 10
        if task.due and task.updated_at.date() <= task.due.date():
            points += 5

    # 3. Syllabus & Revision
    completed_chapters = Syllabus.objects.filter(
        user=user, 
        completed=True
    ).count()
    points += completed_chapters * 50
    
    completed_revisions = Revision.objects.filter(
        user=user,
        completed=True
    ).count()
    points += completed_revisions * 15

    # 4. Tests & Performance
    self_tests = SelfTest.objects.filter(
        user=user
    )
    for t in self_tests:
        points += 20 + float(t.percentage)

    # 5. Habits (all time)
    habits = HabitData.objects.filter(user=user)
    if habits.exists():
        habit_names = habits.values('name').distinct()
        for h in habit_names:
            habit_name = h['name']
            is_good = is_good_habit(habit_name)
            
            logged_dates = set(habits.filter(
                name=habit_name
            ).values_list('date', flat=True))
            
            if is_good:
                points += len(logged_dates) * 10
            else:
                if logged_dates:
                    # Calculate gap days between first log and today
                    min_date = min(logged_dates)
                    max_date = timezone.now().date()
                    total_days = (max_date - min_date).days + 1
                    gap_days = total_days - len(logged_dates)
                    if gap_days > 0:
                        points += gap_days * 10
                        
    return int(points)

def get_global_leaderboard():
    start_of_week, end_of_week = get_week_range()
    users = User.objects.filter(is_active=True)
    leaderboard = []
    
    for user in users:
        pts = calculate_user_points_for_week(user, start_of_week, end_of_week)
        if pts > 0:
            leaderboard.append({
                'user': user,
                'points': pts
            })
            
    # Sort descending by points
    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    
    # Add ranks
    for index, entry in enumerate(leaderboard):
        entry['rank'] = index + 1
        
    return leaderboard
