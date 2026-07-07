from django.shortcuts import render, redirect, get_object_or_404
from .models import Note
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notes/home.html', {'notes': notes})

@login_required
def note_upload(request):
    if request.method == 'POST':
        content = request.POST.get('description', '')
        tags = request.POST.get('tags', '')
        note = Note(content=content, tags=tags, user=request.user)
        note.save()
        return redirect('/notes')
    return render(request, 'notes/note_form.html')

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    note.delete()
    return redirect('/notes')

@login_required
def view_notes(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    return render(request, 'notes/view_notes.html', {'notes': note})
