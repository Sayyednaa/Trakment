from django import forms
from .models import LogEntry

class LogEntryForm(forms.ModelForm):
    class Meta:
        model = LogEntry
        fields = ['subject', 'start_time', 'end_time', 'description']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from revision.models import Subject
            self.fields['subject'].queryset = Subject.objects.filter(user=user)