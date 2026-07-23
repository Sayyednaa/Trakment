from django.shortcuts import render, redirect, get_object_or_404
from .models import Habit, HabitEntry
from collections import defaultdict
from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login')
def habit_list(request):
    """Displays all user habits and allows creating new ones."""
    if request.method == 'POST':
        name = request.POST.get('name')
        habit_type = request.POST.get('habit_type') # 'good' or 'bad'
        is_good = True if habit_type == 'good' else False
        if name:
            Habit.objects.create(name=name, user=request.user, is_good_habit=is_good)
        return redirect('habit_list')

    habits = Habit.objects.filter(user=request.user).order_by('-id')
    
    habit_data = []
    today = datetime.today().date()
    for habit in habits:
        entries = habit.entries.order_by('-date')
        all_dates = list(entries.values_list('date', flat=True))
        
        current_streak = 0
        
        if habit.is_good_habit:
            if all_dates:
                if (today - all_dates[0]).days <= 1:
                    current_streak = 1
                    for i in range(len(all_dates) - 1):
                        if (all_dates[i] - all_dates[i+1]).days == 1:
                            current_streak += 1
                        else:
                            break
        else:
            # Bad Habit Logic
            if all_dates:
                current_streak = (today - all_dates[0]).days
            else:
                current_streak = (today - habit.created_at.date()).days # Fallback

        habit_data.append({
            'id': habit.id,
            'name': habit.name,
            'is_good': habit.is_good_habit,
            'total_entries': len(all_dates),
            'current_streak': current_streak,
        })

    return render(request, 'habit/list.html', {'habits': habit_data})


@login_required(login_url='/login')
def habit_detail(request, habit_id):
    """Main dashboard view for a specific habit tracking."""
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    today_form = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        date = request.POST.get('date')
        if not HabitEntry.objects.filter(habit=habit, date=date).exists():
            HabitEntry.objects.create(habit=habit, date=date)
        return redirect('habit_detail', habit_id=habit.id)

    entries = habit.entries.order_by('-date')
    all_dates = list(entries.values_list('date', flat=True))

    month_year_counts = defaultdict(lambda: defaultdict(int))
    for date in all_dates:
        month = date.strftime("%b")
        year = date.strftime("%Y")
        month_year_counts[month][year] += 1

    all_years = sorted({year for counts in month_year_counts.values() for year in counts})
    chart_data = [["Month"] + all_years]

    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for month in month_order:
        row = [month] + [month_year_counts[month].get(year, 0) for year in all_years]
        chart_data.append(row)

    # Streak Calculations
    today = datetime.today().date()
    longest_streak = 0
    longest_start = "N/A"
    longest_end = "N/A"
    current_streak = 0

    if habit.is_good_habit:
        if all_dates:
            if (today - all_dates[0]).days <= 1:
                current_streak = 1
                for i in range(len(all_dates) - 1):
                    if (all_dates[i] - all_dates[i+1]).days == 1:
                        current_streak += 1
                    else:
                        break

            temp_streak = 1
            temp_end = all_dates[0]
            longest_streak = 1
            longest_end = all_dates[0].strftime('%Y-%m-%d')
            longest_start = all_dates[0].strftime('%Y-%m-%d')

            for i in range(len(all_dates) - 1):
                gap = (all_dates[i] - all_dates[i + 1]).days
                if gap == 1:
                    temp_streak += 1
                else:
                    if temp_streak > longest_streak:
                        longest_streak = temp_streak
                        longest_end = temp_end.strftime('%Y-%m-%d')
                        longest_start = all_dates[i].strftime('%Y-%m-%d')
                    temp_streak = 1
                    temp_end = all_dates[i+1]
            
            if temp_streak > longest_streak:
                longest_streak = temp_streak
                longest_end = temp_end.strftime('%Y-%m-%d')
                longest_start = all_dates[-1].strftime('%Y-%m-%d')
    else:
        # BAD HABIT STREAK LOGIC
        if all_dates:
            current_streak = (today - all_dates[0]).days
            
            if len(all_dates) >= 2:
                # Find the maximum gap between any two entries
                for i in range(len(all_dates) - 1):
                    gap = (all_dates[i] - all_dates[i + 1]).days
                    if gap > longest_streak:
                        longest_streak = gap
                        longest_end = all_dates[i].strftime('%Y-%m-%d')
                        longest_start = all_dates[i + 1].strftime('%Y-%m-%d')
                        
                # Also check if the current streak is the longest
                if current_streak > longest_streak:
                    longest_streak = current_streak
                    longest_end = today.strftime('%Y-%m-%d')
                    longest_start = all_dates[0].strftime('%Y-%m-%d')
            else:
                # Only 1 entry, longest streak is the current streak
                longest_streak = current_streak
                longest_end = today.strftime('%Y-%m-%d')
                longest_start = all_dates[0].strftime('%Y-%m-%d')
        else:
            current_streak = (today - habit.created_at.date()).days
            longest_streak = current_streak

    year_month_counts = defaultdict(lambda: defaultdict(int))
    for date in all_dates:
        year = date.strftime("%Y")
        month = date.strftime("%b")
        year_month_counts[year][month] += 1

    yearly_averages = {year: round(sum(months.values()) / 12, 2) for year, months in year_month_counts.items()}

    weekday_counts = defaultdict(int)
    yearly_counts = defaultdict(int)
    month_year_counts = defaultdict(lambda: defaultdict(int))

    for date in sorted(all_dates):
        month_num = int(date.strftime("%m"))
        year = date.strftime("%Y")
        weekday = date.strftime("%A")

        month_year_counts[month_num][year] += 1
        yearly_counts[year] += 1
        weekday_counts[weekday] += 1

    chart_data = [["Month"] + all_years]
    for month_num in range(1, 13):
        row = [month_num] + [month_year_counts[month_num].get(year, 0) for year in all_years]
        chart_data.append(row)

    weekday_counts = defaultdict(int)
    for date in all_dates:
        weekday = date.strftime("%A") 
        weekday_counts[weekday] += 1

    all_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_activity = {day: weekday_counts.get(day, 0) for day in all_weekdays}

    cumulative_sum = 0
    cumulative_data = []
    for date in sorted(all_dates): 
        cumulative_sum += 1 
        cumulative_data.append((date.strftime("%Y-%m-%d"), cumulative_sum))

    yearly_totals = defaultdict(int)
    for date in all_dates:
        year = date.strftime("%Y") 
        yearly_totals[year] += 1

    monthly_distribution = defaultdict(int)
    for date in all_dates:
        month_name = date.strftime("%b")
        monthly_distribution[month_name] += 1

    return render(request, 'habit/home.html', {
        "habit_obj": habit,
        "yearly_totals": json.dumps(yearly_totals),
        "monthly_distribution": json.dumps(monthly_distribution),
        "weekday_activity": json.dumps(weekday_activity),
        "cumulative_data": json.dumps(cumulative_data),
        "all_years": json.dumps(all_years),
        "chart_data": json.dumps(chart_data),
        "entries": entries,
        "today": today_form,
        "yearly_averages": yearly_averages,
        "longest_streak": longest_streak,
        "longest_streak_range": (longest_start, longest_end) if longest_streak else ("N/A", "N/A"),
        "current_streak": current_streak,
        "weekday_counts": list(weekday_counts.items()),
        "yearly_counts": list(yearly_counts.items()),
    })


@login_required(login_url='/login')
def habit_update(request, habit_id, entry_id):
    """Update habit entry."""
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    entry = get_object_or_404(HabitEntry, id=entry_id, habit=habit)
    today = entry.date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        date = request.POST.get('date')
        if date:
            entry.date = date
            entry.save()
        return redirect('habit_detail', habit_id=habit.id)

    return render(request, 'habit/habit_update.html', {'entry': entry, 'habit': habit, 'today': today})


@login_required(login_url='/login')
def habit_delete(request, habit_id, entry_id):
    """Delete habit entry."""
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    get_object_or_404(HabitEntry, id=entry_id, habit=habit).delete()
    return redirect('habit_detail', habit_id=habit.id)
