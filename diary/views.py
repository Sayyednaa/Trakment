from django.shortcuts import render, redirect, get_object_or_404
from .models import Diary
from django.utils import timezone
from datetime import datetime

def home(request):
    today = timezone.now().date().strftime('%Y-%m-%d')
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled')
        content = request.POST.get('entry')
        date_str = request.POST.get('date')
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = timezone.now()
        
        diary = Diary(title=title, content=content, date=date_obj, user=request.user)
        diary.save()

    diaries = Diary.objects.filter(user=request.user).order_by('-date', '-created_at')
    return render(request, 'diary/diary.html', {'today': today, 'diary': diaries})

def view_diary(request, id):
    diary = get_object_or_404(Diary, id=id, user=request.user)
    return render(request, 'diary/view_diary.html', {'diary': diary})

def delete(request, id):
    diary = get_object_or_404(Diary, id=id, user=request.user)
    diary.delete() # This now triggers the soft delete from SoftDeleteModel
    return redirect('/diary')
