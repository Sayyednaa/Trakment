from django.utils import timezone
from datetime import datetime, timedelta
from .models import Fard, Sunnah, DailyFard, DailySunnah, PrayerTime

def create_daily_records(user):
    """
    Run once per day or on first login/page load
    to create DailyFard & DailySunnah entries for today.
    """
    today = timezone.localdate()

    # Create DailyFard records for all user's fard prayers
    for fard in user.fard_prayers.all():
        daily_fard, created = DailyFard.objects.get_or_create(
            fard=fard,
            user=user,
            date=today,
            defaults={'completed': False, 'completed_time': None}
        )

        # Create DailySunnah records for sunnah prayers linked to this fard
        for sunnah in fard.linked_sunnah.all():
            DailySunnah.objects.get_or_create(
                sunnah=sunnah,
                daily_fard=daily_fard,
                user=user,
                date=today,
                defaults={'completed': False, 'completed_time': None}
            )


# -----------------
# Dynamic Time Calculation
# -----------------
def get_daily_fard_time(daily_fard):
    """Get the prayer time for a daily fard prayer"""
    try:
        # Get the user's prayer times
        prayer_times = daily_fard.user.prayer_times
        
        # Map fard names to prayer time fields
        prayer_time_map = {
            'Fajr': prayer_times.fajr,
            'Juhr': prayer_times.dhuhr,
            'Asr': prayer_times.asr,
            'Maghrib': prayer_times.maghrib,
            'Isha': prayer_times.isha,
        }
        
        prayer_name = daily_fard.fard.name
        if prayer_name in prayer_time_map:
            # Combine today's date with the prayer time
            from django.utils import timezone
            from datetime import datetime, time
            
            prayer_time = prayer_time_map[prayer_name]
            today = timezone.localdate()
            
            # Create a datetime object by combining today's date with prayer time
            return datetime.combine(today, prayer_time)
        
    except Exception as e:
        print(f"Error getting prayer time: {e}")
    
    # Fallback: return current time + some offset based on prayer order
    from django.utils import timezone
    from datetime import timedelta
    
    prayer_order = {'Fajr': 0, 'Dhuhr': 1, 'Asr': 2, 'Maghrib': 3, 'Isha': 4}
    prayer_name = daily_fard.fard.name
    hours_to_add = prayer_order.get(prayer_name, 0) * 3  # 3 hours between prayers
    
    return timezone.now() + timedelta(hours=hours_to_add)

def get_daily_sunnah_time(daily_sunnah):
    """Return datetime for Sunnah using linked DailyFard"""
    fard_dt = get_daily_fard_time(daily_sunnah.daily_fard)
    
    # Define offsets for each sunnah prayer relative to its fard
    offsets = {
        "Fajr Sunnah": -10,  # 10 minutes before Fajr
        "Dhuhr Sunnah Before": -10,  # 10 minutes before Dhuhr
        "Dhuhr Sunnah After": 10,   # 10 minutes after Dhuhr
        "Asr Sunnah": -10,   # 10 minutes before Asr
        "Maghrib Sunnah": 5, # 5 minutes after Maghrib
        "Isha Sunnah": 10,   # 10 minutes after Isha
    }
    
    offset = offsets.get(daily_sunnah.sunnah.name, 0)
    return fard_dt + timedelta(minutes=offset)