from django import forms
from django.utils import timezone
from .models import Task, Project, Milestone, Shift, ShiftTemplate, Note

class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input'
            if isinstance(field.widget, forms.Textarea): field.widget.attrs['rows'] = 3
        for name, field in self.fields.items():
            if name in {'date', 'start_date', 'due_date', 'end_date'}:
                field.widget.attrs['min'] = timezone.localdate().isoformat()

class TaskForm(StyledModelForm):
    class Meta:
        model = Task
        fields = ['title','description','status','priority','start_date','due_date','estimated_minutes','project','milestone','assignee','tags']
        widgets = {'start_date': forms.DateInput(attrs={'type':'date'}), 'due_date': forms.DateInput(attrs={'type':'date'})}
    def clean(self):
        data = super().clean(); today = timezone.localdate()
        start, due = data.get('start_date'), data.get('due_date')
        if start and start < today: self.add_error('start_date', 'Start date cannot be in the past.')
        if due and due < today: self.add_error('due_date', 'Due date cannot be in the past.')
        if start and due and due < start: self.add_error('due_date', 'Due date must be on or after the start date.')
        return data

class ProjectForm(StyledModelForm):
    class Meta:
        model = Project; fields = ['name','description','status','start_date','end_date','color']
        widgets = {'start_date': forms.DateInput(attrs={'type':'date'}), 'end_date': forms.DateInput(attrs={'type':'date'}), 'color': forms.TextInput(attrs={'type':'color','class':'color-input'})}
    def clean(self):
        data = super().clean(); today = timezone.localdate(); start, end = data.get('start_date'), data.get('end_date')
        if start and start < today: self.add_error('start_date', 'Start date cannot be in the past.')
        if end and end < today: self.add_error('end_date', 'End date cannot be in the past.')
        if start and end and end < start: self.add_error('end_date', 'End date must be on or after the start date.')
        return data

class MilestoneForm(StyledModelForm):
    class Meta:
        model = Milestone; fields = ['project','name','description','due_date','status']
        widgets = {'due_date': forms.DateInput(attrs={'type':'date'})}
    def clean_due_date(self):
        value = self.cleaned_data['due_date']
        if value < timezone.localdate(): raise forms.ValidationError('Due date cannot be in the past.')
        return value

class ShiftForm(StyledModelForm):
    template = forms.ModelChoiceField(queryset=ShiftTemplate.objects.none(), required=False, empty_label='Choose a saved schedule…')
    class Meta:
        model = Shift; fields = ['name','date','start_time','end_time','location','notes','color']
        widgets = {'date': forms.DateInput(attrs={'type':'date'}), 'start_time': forms.TimeInput(attrs={'type':'time'}), 'end_time': forms.TimeInput(attrs={'type':'time'}), 'color': forms.TextInput(attrs={'type':'color','class':'color-input'})}
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None: self.fields['template'].queryset = ShiftTemplate.objects.filter(owner=user)
    def clean(self):
        data = super().clean(); today, now = timezone.localdate(), timezone.localtime().time()
        shift_date, start = data.get('date'), data.get('start_time')
        if shift_date and shift_date < today: self.add_error('date', 'Shift date cannot be in the past.')
        if shift_date == today and start and start <= now: self.add_error('start_time', 'Start time must be later than the current time.')
        return data

class ShiftTemplateForm(StyledModelForm):
    class Meta:
        model = ShiftTemplate
        fields = ['name', 'start_time', 'end_time', 'location', 'notes', 'color']
        widgets = {'start_time': forms.TimeInput(attrs={'type':'time'}), 'end_time': forms.TimeInput(attrs={'type':'time'}), 'color': forms.TextInput(attrs={'type':'color','class':'color-input'})}

class ScheduleForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'input'}))
    template = forms.ModelChoiceField(queryset=ShiftTemplate.objects.none(), widget=forms.Select(attrs={'class': 'input'}), empty_label='Choose a schedule template…')
    def __init__(self, *args, user=None, initial=None, **kwargs):
        super().__init__(*args, initial=initial, **kwargs)
        self.fields['date'].widget.attrs['min'] = timezone.localdate().isoformat()
        if user is not None: self.fields['template'].queryset = ShiftTemplate.objects.filter(owner=user)
    def clean_date(self):
        value = self.cleaned_data['date']
        if value < timezone.localdate(): raise forms.ValidationError('Schedule date cannot be in the past.')
        return value

class NoteForm(StyledModelForm):
    class Meta:
        model = Note
        fields = ['title', 'body']
        widgets = {'body': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Write your thoughts…'})}
