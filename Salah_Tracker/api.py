import json
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Fard, Sunnah, DailyFard, DailySunnah, Nafl, QuranReading, Azkaar
from .stats_utils import get_comprehensive_stats
from .helpers import create_daily_records
from datetime import date, datetime

def stringify_keys(d):
    """Recursively stringify dictionary keys safely for JSON serialization"""
    if isinstance(d, dict):
        return {str(k) if isinstance(k, (date, datetime)) else k: stringify_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [stringify_keys(item) for item in d]
    return d

def get_user_from_request(request, data=None):
    """Helper to extract user from GET params or POST data"""
    username = None
    if request.method == 'GET':
        username = request.GET.get('username')
    elif request.method == 'POST' and data:
        username = data.get('username')
        
    if not username:
        return None, JsonResponse({'error': 'username is required'}, status=400)
        
    try:
        user = User.objects.get(username=username)
        return user, None
    except User.DoesNotExist:
        return None, JsonResponse({'error': f'User {username} not found'}, status=404)

@csrf_exempt
def daily_prayers_api(request):
    """Get today's prayers (Fard and Sunnah)"""
    if request.method == 'GET':
        user, error_response = get_user_from_request(request)
        if error_response:
            return error_response
            
        today = timezone.localdate()
        create_daily_records(user)  # Ensure they exist
        
        daily_fards = DailyFard.objects.filter(user=user, date=today).select_related('fard').order_by("fard__name")
        daily_sunnahs = DailySunnah.objects.filter(user=user, date=today).select_related('sunnah__fard').order_by("sunnah__name")
        
        fards_data = [{
            'id': f.id,
            'name': f.fard.name,
            'completed': f.completed,
            'completed_time': f.completed_time.isoformat() if f.completed_time else None
        } for f in daily_fards]
        
        sunnahs_data = [{
            'id': s.id,
            'name': s.sunnah.name,
            'fard_link': s.sunnah.fard.name,
            'completed': s.completed,
            'completed_time': s.completed_time.isoformat() if s.completed_time else None
        } for s in daily_sunnahs]
        
        return JsonResponse({
            'status': 'success',
            'date': str(today),
            'fards': fards_data,
            'sunnahs': sunnahs_data
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def toggle_fard_api(request):
    """Toggle the completion status of a Fard prayer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user, error_response = get_user_from_request(request, data)
            if error_response:
                return error_response
                
            fard_id = data.get('id')
            if not fard_id:
                return JsonResponse({'error': 'id parameter is required'}, status=400)
                
            fard = DailyFard.objects.get(id=fard_id, user=user)
            fard.completed = not fard.completed
            fard.completed_time = timezone.localtime() if fard.completed else None
            fard.save()
            
            return JsonResponse({'status': 'success', 'completed': fard.completed})
        except DailyFard.DoesNotExist:
            return JsonResponse({'error': 'Prayer not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def toggle_sunnah_api(request):
    """Toggle the completion status of a Sunnah prayer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user, error_response = get_user_from_request(request, data)
            if error_response:
                return error_response
                
            sunnah_id = data.get('id')
            if not sunnah_id:
                return JsonResponse({'error': 'id parameter is required'}, status=400)
                
            sunnah = DailySunnah.objects.get(id=sunnah_id, user=user)
            sunnah.completed = not sunnah.completed
            sunnah.completed_time = timezone.localtime() if sunnah.completed else None
            sunnah.save()
            
            return JsonResponse({'status': 'success', 'completed': sunnah.completed})
        except DailySunnah.DoesNotExist:
            return JsonResponse({'error': 'Prayer not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def add_azkaar_api(request):
    """Add a new Zikr entry"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user, error_response = get_user_from_request(request, data)
            if error_response:
                return error_response
                
            name = data.get('name')
            count = int(data.get('count', 1))
            
            if not name:
                return JsonResponse({'error': 'name parameter is required'}, status=400)
                
            azkaar = Azkaar.objects.create(
                user=user,
                name=name,
                count=count
            )
            return JsonResponse({'status': 'success', 'id': azkaar.id, 'name': azkaar.name})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def add_quran_api(request):
    """Add a new Quran reading entry"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user, error_response = get_user_from_request(request, data)
            if error_response:
                return error_response
                
            surah = data.get('surah')
            start_ayah = data.get('start_ayah')
            end_ayah = data.get('end_ayah')
            notes = data.get('notes', '')
            
            if not all([surah, start_ayah, end_ayah]):
                return JsonResponse({'error': 'surah, start_ayah, and end_ayah are required'}, status=400)
                
            quran = QuranReading.objects.create(
                user=user,
                surah=surah,
                start_ayah=int(start_ayah),
                end_ayah=int(end_ayah),
                notes=notes
            )
            return JsonResponse({'status': 'success', 'id': quran.id, 'surah': quran.surah})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def add_nafl_api(request):
    """Add a new Nafl prayer"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user, error_response = get_user_from_request(request, data)
            if error_response:
                return error_response
                
            name = data.get('name')
            if not name:
                return JsonResponse({'error': 'name parameter is required'}, status=400)
                
            nafl = Nafl.objects.create(
                user=user,
                name=name,
                time=timezone.now()
            )
            return JsonResponse({'status': 'success', 'id': nafl.id, 'name': nafl.name})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_stats_api(request):
    """Get comprehensive statistics for the native app"""
    if request.method == 'GET':
        user, error_response = get_user_from_request(request)
        if error_response:
            return error_response
            
        days = int(request.GET.get('days', 30))
        try:
            # Using the existing utility from the web app
            stats = get_comprehensive_stats(user, days)
            
            # Stringify keys (like datetime.date) since JsonResponse fails on non-string keys
            stats = stringify_keys(stats)
            
            # Additional simple top-level stats common for dashboards
            today = timezone.now().date()
            fard_completed = DailyFard.objects.filter(user=user, date=today, completed=True).count()
            fard_total = DailyFard.objects.filter(user=user, date=today).count()
            
            return JsonResponse({
                'status': 'success',
                'summary': {
                    'fard_completed_today': fard_completed,
                    'fard_total_today': fard_total,
                },
                'detailed_stats': stats
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def get_next_prayer_api(request):
    """Get the next prayer based on current time and user's PrayerTime"""
    if request.method == 'GET':
        user, error_response = get_user_from_request(request)
        if error_response:
            return error_response

        if not hasattr(user, 'prayer_times'):
            return JsonResponse({'error': 'Prayer times not set for this user'}, status=404)

        prayer_times = user.prayer_times
        current_time = timezone.localtime().time()

        prayers = [
            ('Fajr', prayer_times.fajr),
            ('Dhuhr', prayer_times.dhuhr),
            ('Asr', prayer_times.asr),
            ('Maghrib', prayer_times.maghrib),
            ('Isha', prayer_times.isha),
        ]

        next_prayer = None
        next_prayer_time = None
        next_index = None

        for i, (name, p_time) in enumerate(prayers):
            if p_time and current_time < p_time:
                next_prayer = name
                next_prayer_time = p_time
                next_index = i
                break

        is_tomorrow = False
        if next_prayer is None:
            next_prayer = 'Fajr'
            next_prayer_time = prayers[0][1]
            next_index = 0
            is_tomorrow = True

        previous_index = (next_index - 1) % len(prayers)
        previous_prayer, previous_prayer_time = prayers[previous_index]

        return JsonResponse({
            'status': 'success',
            'next_prayer': next_prayer,
            'time': next_prayer_time.strftime('%H:%M:%S') if next_prayer_time else None,
            'is_tomorrow': is_tomorrow,
            'previous_prayer': previous_prayer,
            'previous_time': previous_prayer_time.strftime('%H:%M:%S') if previous_prayer_time else None,
        })

    return JsonResponse({'error': 'Method not allowed'}, status=405)