from django.shortcuts import render, redirect, get_object_or_404
from .models import Password
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    if request.method == 'POST':
        platform = request.POST.get('website', '')
        password = request.POST.get('password', '')
        username = request.POST.get('username', '')
        
        data = Password(platform=platform, username=username, pass_hash=password, user=request.user)
        data.save()
        return redirect('/password')
        
    passwords = Password.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'password/home.html', {'passwords': passwords})

@login_required
def update(request, id):
    data = get_object_or_404(Password, id=id, user=request.user)
    if request.method == 'POST':
        data.platform = request.POST.get('website', '')
        data.pass_hash = request.POST.get('password', '')
        data.username = request.POST.get('username', '')
        data.save()
        return redirect('/password')
        
    return render(request, 'password/password_update.html', {'password': data})

@login_required
def delete(request, id):
    data = get_object_or_404(Password, id=id, user=request.user)
    data.delete()
    return redirect('/password')