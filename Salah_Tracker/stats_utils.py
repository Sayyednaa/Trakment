# stats_utils.py
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Sum, Avg, Q
from .models import *

def get_prayer_stats(user, days=30):
    """Get comprehensive prayer statistics for a user"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fard prayers stats
    fard_prayers = DailyFard.objects.filter(
        user=user, 
        date__range=[start_date, end_date]
    )
    
    total_fard = fard_prayers.count()
    completed_fard = fard_prayers.filter(completed=True).count()
    fard_completion_rate = (completed_fard / total_fard * 100) if total_fard > 0 else 0
    
    # Sunnah prayers stats
    sunnah_prayers = DailySunnah.objects.filter(
        user=user, 
        date__range=[start_date, end_date]
    )
    
    total_sunnah = sunnah_prayers.count()
    completed_sunnah = sunnah_prayers.filter(completed=True).count()
    sunnah_completion_rate = (completed_sunnah / total_sunnah * 100) if total_sunnah > 0 else 0
    
    # Daily completion streaks
    daily_completion = {}
    for single_date in (start_date + timedelta(n) for n in range(days + 1)):
        day_fard = fard_prayers.filter(date=single_date, completed=True).count()
        day_sunnah = sunnah_prayers.filter(date=single_date, completed=True).count()
        daily_completion[single_date] = {
            'fard': day_fard,
            'sunnah': day_sunnah,
            'total_prayers': day_fard + day_sunnah
        }
    
    # Prayer-wise completion rates
    prayer_wise_stats = {}
    for fard in Fard.objects.filter(user=user):
        fard_completed = fard_prayers.filter(fard=fard, completed=True).count()
        fard_total = fard_prayers.filter(fard=fard).count()
        prayer_wise_stats[fard.name] = {
            'completed': fard_completed,
            'total': fard_total,
            'rate': (fard_completed / fard_total * 100) if fard_total > 0 else 0
        }
    
    return {
        'period': f"Last {days} days",
        'fard_stats': {
            'total': total_fard,
            'completed': completed_fard,
            'completion_rate': round(fard_completion_rate, 1),
            'missed': total_fard - completed_fard
        },
        'sunnah_stats': {
            'total': total_sunnah,
            'completed': completed_sunnah,
            'completion_rate': round(sunnah_completion_rate, 1),
            'missed': total_sunnah - completed_sunnah
        },
        'daily_completion': daily_completion,
        'prayer_wise_stats': prayer_wise_stats,
        'total_prayers': total_fard + total_sunnah,
        'total_completed': completed_fard + completed_sunnah,
        'overall_completion_rate': round(
            ((completed_fard + completed_sunnah) / (total_fard + total_sunnah) * 100) 
            if (total_fard + total_sunnah) > 0 else 0, 1
        )
    }

def get_quran_stats(user, days=30):
    """Get Quran reading statistics"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    quran_readings = QuranReading.objects.filter(
        user=user, 
        date__range=[start_date, end_date]
    )
    
    total_sessions = quran_readings.count()
    total_ayahs = sum((q.end_ayah - q.start_ayah + 1) for q in quran_readings)
    
    # Daily reading consistency
    reading_days = quran_readings.values('date').annotate(
        sessions=Count('id'),
        ayahs_read=Sum('end_ayah') - Sum('start_ayah')
    ).order_by('date')
    
    return {
        'total_sessions': total_sessions,
        'total_ayahs': total_ayahs,
        'average_ayahs_per_session': round(total_ayahs / total_sessions, 1) if total_sessions > 0 else 0,
        'reading_days_count': len(set(q.date for q in quran_readings)),
        'reading_consistency': round((len(set(q.date for q in quran_readings)) / days) * 100, 1),
        'daily_breakdown': list(reading_days)
    }

def get_azkaar_stats(user, days=30):
    """Get Azkaar/Dhikr statistics"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    azkaar = Azkaar.objects.filter(
        user=user, 
        date__range=[start_date, end_date]
    )
    
    total_azkaar = azkaar.count()
    total_count = azkaar.aggregate(total=Sum('count'))['total'] or 0
    
    # Breakdown by type
    azkaar_by_type = azkaar.values('name').annotate(
        total_count=Sum('count'),
        entries=Count('id')
    ).order_by('-total_count')
    
    most_frequent = azkaar_by_type.first()
    
    return {
        'total_entries': total_azkaar,
        'total_count': total_count,
        'average_per_day': round(total_count / days, 1),
        'most_frequent': most_frequent['name'] if most_frequent else 'None',
        'most_frequent_count': most_frequent['total_count'] if most_frequent else 0,
        'breakdown_by_type': list(azkaar_by_type)
    }

def get_nafl_stats(user, days=30):
    """Get Nafl prayer statistics"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    nafl_prayers = Nafl.objects.filter(
        user=user, 
        time__date__range=[start_date, end_date]
    )
    
    total_nafl = nafl_prayers.count()
    
    # Nafl by time of day - database-agnostic approach
    nafl_by_hour = {}
    for nafl in nafl_prayers:
        hour = nafl.time.hour
        nafl_by_hour[hour] = nafl_by_hour.get(hour, 0) + 1
    
    # Convert to list of dictionaries for consistency
    nafl_by_hour_list = [{'hour': hour, 'count': count} 
                        for hour, count in sorted(nafl_by_hour.items())]
    
    return {
        'total_nafl': total_nafl,
        'average_per_day': round(total_nafl / days, 1) if days > 0 else total_nafl,
        'nafl_by_hour': nafl_by_hour_list
    }

def get_comprehensive_stats(user, days=30):
    """Get all statistics in one call"""
    return {
        'prayer_stats': get_prayer_stats(user, days),
        'quran_stats': get_quran_stats(user, days),
        'azkaar_stats': get_azkaar_stats(user, days),
        'nafl_stats': get_nafl_stats(user, days),
        'period_days': days
    }