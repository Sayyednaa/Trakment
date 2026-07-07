from django.shortcuts import render, redirect
from .models import data
from collections import defaultdict
from datetime import datetime, timedelta
from django.http import JsonResponse
import csv
import json
import os
import numpy as np
from django.conf import settings


def home(request):
    """Main dashboard view for habit tracking."""
    today_form = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        data.objects.create(name=name, date=date, user=request.user)
        return redirect('/data/')

    habit = data.objects.filter(user=request.user)
    all_dates = list(data.objects.values_list('date', flat=True))

    # Organize data: {Month: {Year: Count}}
    month_year_counts = defaultdict(lambda: defaultdict(int))
    for date in all_dates:
        month = date.strftime("%b")
        year = date.strftime("%Y")
        month_year_counts[month][year] += 1

    # Prepare chart data
    all_years = sorted({year for counts in month_year_counts.values() for year in counts})
    chart_data = [["Month"] + all_years]

    # Ensure proper month sorting
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for month in month_order:
        row = [month] + [month_year_counts[month].get(year, 0) for year in all_years]
        chart_data.append(row)

    # Streak Calculations
    all_dates = list(data.objects.values_list('date', flat=True).order_by('-date'))
    today = datetime.today().date()
    longest_streak = 0
    current_streak = (today - all_dates[0]).days if all_dates else 0

    for i in range(len(all_dates) - 1):
        gap = (all_dates[i] - all_dates[i + 1]).days - 1
        if gap > longest_streak:
            longest_streak = gap
            longest_start = (all_dates[i + 1] + timedelta(days=1)).strftime('%Y-%m-%d')
            longest_end = (all_dates[i] - timedelta(days=1)).strftime('%Y-%m-%d')

    # Yearly Average Calculation
    year_month_counts = defaultdict(lambda: defaultdict(int))
    for date in all_dates:
        year = date.strftime("%Y")
        month = date.strftime("%b")
        year_month_counts[year][month] += 1

    yearly_averages = {year: round(sum(months.values()) / 12, 2) for year, months in year_month_counts.items()}

    # Additional Data Processing
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

    # Create JSON chart data
    chart_data = [["Month"] + all_years]
    for month_num in range(1, 13):
        row = [month_num] + [month_year_counts[month_num].get(year, 0) for year in all_years]
        chart_data.append(row)

    weekday_counts = defaultdict(int)
    for date in all_dates:
        weekday = date.strftime("%A")  # Get full weekday name (Monday, Tuesday, etc.)
        weekday_counts[weekday] += 1

    # Ensure all days exist (even if count is 0)
    all_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_activity = {day: weekday_counts.get(day, 0) for day in all_weekdays}

    cumulative_sum = 0
    cumulative_data = []
    for date in sorted(all_dates):  # Ensure dates are sorted
        cumulative_sum += 1  # Assuming each date represents one entry
        cumulative_data.append((date.strftime("%Y-%m-%d"), cumulative_sum))

    yearly_totals = defaultdict(int)

    for date in all_dates:
        year = date.strftime("%Y")  # Extract year
        yearly_totals[year] += 1  # Count occurrences

    # Step 2: Convert to JSON
    yearly_totals_json = json.dumps(yearly_totals)


    monthly_distribution = defaultdict(int)

    for date in all_dates:
        month_name = date.strftime("%b")  # Get month name (e.g., "Jan", "Feb")
        monthly_distribution[month_name] += 1  # Count occurrences

    # Step 2: Convert to JSON
    monthly_distribution_json = json.dumps(monthly_distribution)


    return render(request, 'habit/home.html', {
        "yearly_totals": yearly_totals_json,
        "monthly_distribution": monthly_distribution_json,
        "weekday_activity": json.dumps(weekday_activity),
        "cumulative_data": json.dumps(cumulative_data),

        "all_years": json.dumps(all_years),
        "chart_data": json.dumps(chart_data),
        "habit": habit,
        "today": today_form,
        "yearly_averages": yearly_averages,
        "longest_streak": longest_streak,
        "longest_streak_range": (longest_start, longest_end) if longest_streak else ("N/A", "N/A"),
        "current_streak": current_streak,
        "weekday_counts": list(weekday_counts.items()),
        "yearly_counts": list(yearly_counts.items()),
    })


def update(request, id):
    """Update habit entry."""
    entry = data.objects.filter(user=request.user).get(id=id)
    today = entry.date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        entry.name = request.POST.get('name')
        entry.date = request.POST.get('date')
        entry.save()
        return redirect('/data/')

    return render(request, 'habit/habit_update.html', {'data': entry, 'today': today})


def delete(request, id):
    """Delete habit entry."""
    data.objects.filter(user=request.user).get(id=id).delete()
    return redirect('/data/')
