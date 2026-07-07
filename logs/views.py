from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import LogEntry
from .forms import LogEntryForm

@login_required
def log_list(request):
    if request.method == 'POST':
        form = LogEntryForm(request.POST, user=request.user)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            return redirect('/logs/')
    else:
        form = LogEntryForm(user=request.user)
    
    logs = LogEntry.objects.filter(user=request.user)
    return render(request, 'logs/list.html', {'logs': logs, 'form': form})

@login_required
def log_create(request):
    if request.method == 'POST':
        form = LogEntryForm(request.POST, user=request.user)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            return redirect('/logs/')
    else:
        form = LogEntryForm(user=request.user)
    return render(request, 'logs/create.html', {'form': form})

@login_required
def log_update(request, pk):
    log = LogEntry.objects.get(pk=pk, user=request.user)
    if request.method == 'POST':
        form = LogEntryForm(request.POST, instance=log, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('/logs/')
    else:
        form = LogEntryForm(instance=log, user=request.user)
    return render(request, 'logs/update.html', {'form': form, 'log': log})

@login_required
def log_delete(request, pk):
    log = LogEntry.objects.get(pk=pk, user=request.user)
    if request.method == 'POST':
        log.delete()
        return redirect('/logs/')
    return render(request, 'logs/delete.html', {'log': log})