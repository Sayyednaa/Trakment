import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum, F
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .import tests
from .models import Fard, Sunnah, Nafl, QuranReading, Azkaar, PrayerTime, DailyFard, DailySunnah
from .helpers import create_daily_records, get_daily_fard_time, get_daily_sunnah_time
from .stats_utils import get_comprehensive_stats  # Import the new stats functions
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import PrayerTime
import json

@login_required
def home(request):
    try:
        prayer_times = user.prayer_times
        if prayer_times:
            print("=== STORED PRAYER TIMES ===")
            print(f"Fajr: {prayer_times.fajr}")
            print(f"Dhuhr: {prayer_times.dhuhr}")
            print(f"Asr: {prayer_times.asr}")
            print(f"Maghrib: {prayer_times.maghrib}")
            print(f"Isha: {prayer_times.isha}")
        else:
            print("=== NO PRAYER TIMES SET ===")
    except Exception as e:
        print(f"Error reading prayer times: {e}")
    user = request.user
    today = timezone.localdate()
    now = timezone.localtime()

    # Create daily records
    create_daily_records(user)

    # Handle POST requests
    if request.method == "POST":
        # Mark Fard/Sunnah done
        fard_id = request.POST.get("mark_fard_done")
        sunnah_id = request.POST.get("mark_sunnah_done")

        if fard_id:
            fard = get_object_or_404(DailyFard, id=fard_id, user=user)
            fard.completed = True
            fard.completed_time = now
            fard.save()

        if sunnah_id:
            sunnah = get_object_or_404(DailySunnah, id=sunnah_id, user=user)
            sunnah.completed = True
            sunnah.completed_time = now
            sunnah.save()

        # Add Azkaar
        if "add_azkaar" in request.POST:
            Azkaar.objects.create(
                user=user,
                name=request.POST.get("zikr_name"),
                count=int(request.POST.get("zikr_count", 1)),
                date=today
            )

        # Add Quran reading
        elif "add_quran" in request.POST:
            QuranReading.objects.create(
                user=user,
                surah=request.POST.get("surah"),
                start_ayah=int(request.POST.get("start_ayah")),
                end_ayah=int(request.POST.get("end_ayah")),
                notes=request.POST.get("notes"),
                date=today
            )

        return redirect("/")

    # Get today's data
    daily_fard = DailyFard.objects.filter(user=user, date=today).order_by("fard__name")
    daily_sunnah = DailySunnah.objects.filter(user=user, date=today).order_by("sunnah__name")

    fard_with_times = [(f, get_daily_fard_time(f)) for f in daily_fard]
    sunnah_with_times = [(s, get_daily_sunnah_time(s)) for s in daily_sunnah]

    # DEBUG: Print prayer times to console
    print("Current time:", now.time())
    for f, time_value in fard_with_times:
        print(f"Prayer: {f.fard.name}, Time: {time_value.time()}")

    # Find upcoming prayer - FIXED VERSION
    upcoming_prayer = None
    upcoming_prayer_time = None

    # Sort prayers by their actual time
    sorted_fard_with_times = sorted(fard_with_times, key=lambda x: x[1].time())

    for f, time_value in sorted_fard_with_times:
        prayer_time = time_value.time()
        current_time = now.time()

        print(f"Checking {f.fard.name}: {prayer_time} > {current_time} = {prayer_time > current_time}")

        if prayer_time > current_time:
            upcoming_prayer = f
            upcoming_prayer_time = time_value
            break

    # If no prayer found for today, get the first prayer of the next day
    if not upcoming_prayer and sorted_fard_with_times:
        upcoming_prayer = sorted_fard_with_times[0][0]
        upcoming_prayer_time = sorted_fard_with_times[0][1]
        # Add one day to the time since it's for tomorrow
        from datetime import timedelta
        upcoming_prayer_time = upcoming_prayer_time + timedelta(days=1)

    # DEBUG: Print result
    if upcoming_prayer:
        print(f"UPCOMING PRAYER: {upcoming_prayer.fard.name} at {upcoming_prayer_time.time()}")
    else:
        print("NO UPCOMING PRAYER FOUND")



    context = {
        "fard_with_times": fard_with_times,
        "sunnah_with_times": sunnah_with_times,
        "upcoming_prayer": upcoming_prayer,
        "upcoming_prayer_time": upcoming_prayer_time,  # Make sure to pass this to template
        "azkaar_today": Azkaar.objects.filter(user=user, date=today),

        "quran_today": QuranReading.objects.filter(user=user, date=today),
        "prayer_times": getattr(user, "prayer_times", None),
    }

    return render(request, "salah_tracker/home.html", context)


@csrf_exempt
@login_required
def toggle_fard(request):
    if request.method == "POST":
        fard = get_object_or_404(DailyFard, id=request.POST.get("id"), user=request.user)
        fard.completed = not fard.completed
        fard.completed_time = timezone.localtime() if fard.completed else None
        fard.save()
        return JsonResponse({"status": fard.completed})


@csrf_exempt
@login_required
def toggle_sunnah(request):
    if request.method == "POST":
        sunnah = get_object_or_404(DailySunnah, id=request.POST.get("id"), user=request.user)
        sunnah.completed = not sunnah.completed
        sunnah.completed_time = timezone.localtime() if sunnah.completed else None
        sunnah.save()
        return JsonResponse({"status": sunnah.completed})


@login_required
def profile(request):
    return redirect('/profile')


@login_required
def add_nafl(request):
    if request.method == "POST":
        Nafl.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            time=timezone.now()
        )
        return redirect("home")
    return render(request, "add_nafl.html")


@login_required
def add_quran_reading(request):
    if request.method == "POST":
        QuranReading.objects.create(
            user=request.user,
            surah=request.POST.get("surah"),
            start_ayah=int(request.POST.get("start_ayah")),
            end_ayah=int(request.POST.get("end_ayah")),
            notes=request.POST.get("notes")
        )
        return redirect("home")
    return render(request, "add_quran.html")


@login_required
def add_azkaar(request):
    if request.method == "POST":
        Azkaar.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            count=int(request.POST.get("count", 1))
        )
        return redirect("home")
    return render(request, "add_azkaar.html")


@login_required
def prayer_times(request):
    if request.method == "POST":
        PrayerTime.objects.create(
            user=request.user,
            name=request.POST.get("name"),
            time=request.POST.get("time")
        )
        return redirect("home")
    return render(request, "add_prayer_time.html")


# Enhanced Stats Views with New Analytics

@login_required
def stats(request):
    """Main stats dashboard - enhanced with new analytics"""
    user = request.user
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    # Get comprehensive stats from new utility functions
    days = int(request.GET.get('days', 30))
    comprehensive_stats = get_comprehensive_stats(user, days)

    # Original stats calculations (for backward compatibility)
    # Fard completion stats
    fard_stats = (
        DailyFard.objects.filter(user=user, date__gte=last_30_days)
        .values("date")
        .annotate(
            completed_count=Count("id", filter=Q(completed=True)),
            total=Count("id")
        )
        .order_by("date")
    )

    fard_labels = [str(x["date"]) for x in fard_stats]
    fard_completion = [
        round((x["completed_count"] / x["total"]) * 100, 2) if x["total"] > 0 else 0
        for x in fard_stats
    ]

    # Streak calculation
    streak, max_streak = 0, 0
    for day in range(30):
        day_date = today - timedelta(days=day)
        prayers = DailyFard.objects.filter(user=user, date=day_date)
        if prayers.exists() and prayers.filter(completed=True).count() == prayers.count():
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # Worship score
    worship_score = {
        "Fard": DailyFard.objects.filter(user=user, completed=True, date__gte=last_30_days).count(),
        "Sunnah": DailySunnah.objects.filter(user=user, completed=True, date__gte=last_30_days).count(),
        "Nafl": Nafl.objects.filter(user=user, time__date__gte=last_30_days).count(),
        "Quran": QuranReading.objects.filter(user=user, date__gte=last_30_days).count(),
        "Azkaar": Azkaar.objects.filter(user=user, date__gte=last_30_days).aggregate(
            total=Sum("count"))["total"] or 0,
    }

    # Quran stats
    quran_stats = (
        QuranReading.objects.filter(user=user, date__gte=last_30_days)
        .values("date")
        .annotate(verses=Avg(F("end_ayah") - F("start_ayah") + 1))
        .order_by("date")
    )

    context = {
        # Original stats data
        "fard_labels": json.dumps(fard_labels),
        "fard_completion": json.dumps(fard_completion),
        "streak": max_streak,
        "worship_labels": json.dumps(list(worship_score.keys())),
        "worship_data": json.dumps(list(worship_score.values())),
        "quran_labels": json.dumps([str(x["date"]) for x in quran_stats]),
        "quran_verses": json.dumps([int(x["verses"] or 0) for x in quran_stats]),
        "quran_days": QuranReading.objects.filter(user=user, date__gte=last_30_days).values("date").distinct().count(),

        # New comprehensive stats
        "comprehensive_stats": comprehensive_stats,
        "selected_days": days,
        "time_periods": [7, 30, 90, 365]
    }

    return render(request, "salah_tracker/stats.html", context)
# In your views.py - update the stats views section:

@login_required
def dashboard_stats(request):
    """New comprehensive dashboard with all statistics"""
    try:
        days = int(request.GET.get('days', 30))
        stats = get_comprehensive_stats(request.user, days)

        context = {
            'stats': stats,
            'selected_days': days,
            'time_periods': [7, 30, 90, 365]
        }

        return render(request, ' dashboard.html', context)
    except Exception as e:
        # Handle any errors gracefully
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f"Error loading stats: {str(e)}")

@login_required
def prayer_detail_stats(request):
    """Detailed prayer statistics"""
    try:
        days = int(request.GET.get('days', 30))
        stats = get_comprehensive_stats(request.user, days)

        context = {
            'prayer_stats': stats['prayer_stats'],
            'selected_days': days,
            'time_periods': [7, 30, 90, 365]
        }

        return render(request, 'salah_tracker/prayer_detail.html', context)
    except Exception as e:
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f"Error loading prayer stats: {str(e)}")

@login_required
def quran_stats_view(request):
    """Quran reading statistics"""
    try:
        days = int(request.GET.get('days', 30))
        stats = get_comprehensive_stats(request.user, days)

        context = {
            'quran_stats': stats['quran_stats'],
            'selected_days': days,
            'time_periods': [7, 30, 90, 365]
        }

        return render(request, 'salah_tracker/quran_stats.html', context)
    except Exception as e:
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f"Error loading Quran stats: {str(e)}")

@login_required
def azkaar_stats_view(request):
    """Azkaar/Dhikr statistics"""
    try:
        days = int(request.GET.get('days', 30))
        stats = get_comprehensive_stats(request.user, days)

        context = {
            'azkaar_stats': stats['azkaar_stats'],
            'selected_days': days,
            'time_periods': [7, 30, 90, 365]
        }

        return render(request, 'salah_tracker/azkaar_stats.html', context)
    except Exception as e:
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f"Error loading Azkaar stats: {str(e)}")

@login_required
def nafl_stats_view(request):
    """Nafl prayer statistics"""
    try:
        days = int(request.GET.get('days', 30))
        stats = get_comprehensive_stats(request.user, days)

        context = {
            'nafl_stats': stats['nafl_stats'],
            'selected_days': days,
            'time_periods': [7, 30, 90, 365]
        }

        return render(request, 'salah_tracker/nafl_stats.html', context)
    except Exception as e:
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f"Error loading Nafl stats: {str(e)}")





@require_GET
def prayer_times_api(request):
    """
    API endpoint that returns prayer times for a specific user
    URL: /api/prayer-times/?username=john_doe
    """
    username = request.GET.get('username')

    if not username:
        return JsonResponse(
            {'error': 'Username parameter is required. Use ?username=your_username'},
            status=400
        )

    try:
        prayer_times = PrayerTime.objects.get(user__username=username)

        data = {
            'username': username,
            'fajr': prayer_times.fajr.strftime('%H:%M:%S'),
            'dhuhr': prayer_times.dhuhr.strftime('%H:%M:%S'),
            'asr': prayer_times.asr.strftime('%H:%M:%S'),
            'maghrib': prayer_times.maghrib.strftime('%H:%M:%S'),
            'isha': prayer_times.isha.strftime('%H:%M:%S'),
        }

        return JsonResponse(data)

    except PrayerTime.DoesNotExist:
        return JsonResponse(
            {'error': f'Prayer times not found for user: {username}'},
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'An error occurred: {str(e)}'},
            status=500
        )

def api_docs(request):
    """Render the API documentation page"""
    return render(request, 'salah_tracker/api_docs.html')