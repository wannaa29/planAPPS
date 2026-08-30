from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.utils import timezone
from .forms import TaskForm, ProjectForm, MilestoneForm, ShiftForm, ShiftTemplateForm, ScheduleForm, NoteForm
from .models import Task, Project, ProjectMembership, Milestone, Shift, ShiftTemplate, Notification, ReminderPreference, Note

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(); ReminderPreference.objects.create(user=user); login(request, user); return redirect('dashboard')
    else: form = UserCreationForm()
    for field in form.fields.values(): field.widget.attrs['class'] = 'input'
    return render(request, 'registration/register.html', {'form': form})

def _visible_projects(user):
    return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()

def _seed_demo(user):
    if Project.objects.filter(owner=user).exists(): return
    today = timezone.localdate()
    project = Project.objects.create(owner=user, name='Website refresh', description='A focused launch plan for the new marketing site.', status='ACTIVE', start_date=today-timedelta(days=8), end_date=today+timedelta(days=21), color='#4F46E5')
    ProjectMembership.objects.create(project=project, user=user, role='OWNER')
    milestone = Milestone.objects.create(project=project, name='Public launch', due_date=today+timedelta(days=12), status='IN_PROGRESS')
    Task.objects.create(created_by=user, project=project, milestone=milestone, assignee=user, title='Finalize homepage copy', status='IN_PROGRESS', priority='HIGH', due_date=today, estimated_minutes=90)
    Task.objects.create(created_by=user, project=project, assignee=user, title='Review analytics events', status='TODO', priority='MEDIUM', due_date=today+timedelta(days=2), estimated_minutes=45)
    Task.objects.create(created_by=user, project=project, title='Set up launch checklist', status='DONE', priority='LOW', due_date=today-timedelta(days=1), estimated_minutes=30)
    template = ShiftTemplate.objects.create(owner=user, name='Morning shift', start_time='08:00', end_time='16:00', location='HQ · Floor 2')
    Shift.objects.create(owner=user, template=template, name=template.name, date=today, start_time=template.start_time, end_time=template.end_time, location=template.location, color=template.color)
    Shift.objects.create(owner=user, template=template, name=template.name, date=today+timedelta(days=1), start_time=template.start_time, end_time=template.end_time, location=template.location, color=template.color)
    Notification.objects.create(recipient=user, type='DEADLINE_WARNING', title='Public launch is coming up', message='Your milestone is due in 12 days.')

def _ensure_template(user):
    if not ShiftTemplate.objects.filter(owner=user).exists():
        ShiftTemplate.objects.create(owner=user, name='Morning shift', start_time='08:00', end_time='16:00', location='')

@login_required
def dashboard(request):
    return render(request, 'planner/app_home.html')

@login_required
def schedule_dashboard(request):
    _seed_demo(request.user)
    _ensure_template(request.user)
    today = timezone.localdate(); projects = _visible_projects(request.user); scope = Q(created_by=request.user) | Q(assignee=request.user)
    todays_tasks = Task.objects.filter(scope, due_date=today).distinct()
    overdue = Task.objects.filter(scope, due_date__lt=today).exclude(status__in=['DONE','CANCELLED']).distinct()
    shifts_today = Shift.objects.filter(owner=request.user, date=today)
    upcoming_shifts = Shift.objects.filter(owner=request.user, date__gt=today)[:3]
    deadlines = Task.objects.filter(scope, due_date__gte=today, due_date__lte=today+timedelta(days=14)).exclude(status__in=['DONE','CANCELLED']).order_by('due_date')[:4]
    milestones_upcoming = Milestone.objects.filter(project__in=projects, due_date__gte=today).order_by('due_date')[:3]
    return render(request, 'planner/schedule_dashboard.html', {'today':today,'todays_tasks':todays_tasks,'overdue':overdue,'shifts_today':shifts_today,'upcoming_shifts':upcoming_shifts,'deadlines':deadlines,'milestones':milestones_upcoming,'projects':projects[:4],'notifications':request.user.notifications.all()[:4],'unread_count':request.user.notifications.filter(read=False).count()})

@login_required
def tasks(request):
    qs = Task.objects.filter(Q(created_by=request.user) | Q(assignee=request.user)).select_related('project','assignee').distinct(); status = request.GET.get('status'); query = request.GET.get('q','').strip()
    if status: qs = qs.filter(status=status)
    if query: qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, 'planner/list.html', {'page_title':'Tasks','subtitle':'Keep the next actions moving.','items':qs,'item_type':'task','status_choices':Task.STATUS_CHOICES,'active_status':status,'query':query})

@login_required
def task_create(request):
    form = TaskForm(request.POST or None); form.fields['project'].queryset = _visible_projects(request.user); form.fields['assignee'].queryset = request.user.__class__.objects.filter(id=request.user.id)
    if form.is_valid():
        task=form.save(commit=False); task.created_by=request.user; task.save(); messages.success(request,'Task added to your plan.'); return redirect('tasks')
    return render(request, 'planner/form.html', {'form':form,'page_title':'New task','back_url':'tasks','offline_kind':'task'})

@login_required
def task_toggle(request, pk):
    task = get_object_or_404(Task, Q(created_by=request.user) | Q(assignee=request.user), pk=pk); task.status = 'DONE' if task.status != 'DONE' else 'TODO'; task.save(update_fields=['status']); return redirect(request.META.get('HTTP_REFERER','dashboard'))

@login_required
def projects(request):
    return render(request, 'planner/list.html', {'page_title':'Projects','subtitle':'A clear view of the work that matters.','items':_visible_projects(request.user),'item_type':'project'})

@login_required
def project_create(request):
    form=ProjectForm(request.POST or None)
    if form.is_valid():
        project=form.save(commit=False); project.owner=request.user; project.save(); ProjectMembership.objects.create(project=project,user=request.user,role='OWNER'); messages.success(request,'Project created.'); return redirect('projects')
    return render(request,'planner/form.html',{'form':form,'page_title':'New project','back_url':'projects'})

@login_required
def project_edit(request, pk):
    project = get_object_or_404(_visible_projects(request.user), pk=pk)
    if project.owner_id != request.user.id and not ProjectMembership.objects.filter(project=project, user=request.user, role='MANAGER').exists():
        return redirect('projects')
    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid(): form.save(); messages.success(request, 'Project updated.'); return redirect('projects')
    return render(request, 'planner/form.html', {'form': form, 'page_title': 'Edit project', 'back_url': 'projects'})

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, owner=request.user, pk=pk)
    if request.method == 'POST': project.delete(); messages.success(request, 'Project deleted.'); return redirect('projects')
    return render(request, 'planner/confirm_delete.html', {'object': project, 'back_url': 'projects', 'object_type': 'project'})

@login_required
def milestones(request):
    return render(request,'planner/list.html',{'page_title':'Milestones','subtitle':'Keep the important checkpoints in sight.','items':Milestone.objects.filter(project__in=_visible_projects(request.user)).select_related('project'),'item_type':'milestone'})

@login_required
def milestone_create(request):
    form=MilestoneForm(request.POST or None); form.fields['project'].queryset=_visible_projects(request.user)
    if form.is_valid(): form.save(); messages.success(request,'Milestone added.'); return redirect('milestones')
    return render(request,'planner/form.html',{'form':form,'page_title':'New milestone','back_url':'milestones'})

@login_required
def milestone_edit(request, pk):
    milestone = get_object_or_404(Milestone, project__in=_visible_projects(request.user), pk=pk)
    form = MilestoneForm(request.POST or None, instance=milestone); form.fields['project'].queryset = _visible_projects(request.user)
    if form.is_valid(): form.save(); messages.success(request, 'Milestone updated.'); return redirect('milestones')
    return render(request, 'planner/form.html', {'form': form, 'page_title': 'Edit milestone', 'back_url': 'milestones'})

@login_required
def milestone_delete(request, pk):
    milestone = get_object_or_404(Milestone, project__owner=request.user, pk=pk)
    if request.method == 'POST': milestone.delete(); messages.success(request, 'Milestone deleted.'); return redirect('milestones')
    return render(request, 'planner/confirm_delete.html', {'object': milestone, 'back_url': 'milestones', 'object_type': 'milestone'})

@login_required
def shifts(request):
    return redirect('calendar')

@login_required
def shift_create(request):
    return redirect('schedule_create')

@login_required
def schedule_create(request):
    _ensure_template(request.user)
    initial = {'date': request.GET.get('date')} if request.GET.get('date') else None
    form = ScheduleForm(request.POST or None, user=request.user, initial=initial)
    if form.is_valid():
        template = form.cleaned_data['template']; date_value = form.cleaned_data['date']
        Shift.objects.create(owner=request.user, template=template, name=template.name, date=date_value, start_time=template.start_time, end_time=template.end_time, location=template.location, notes=template.notes, color=template.color)
        messages.success(request, 'Schedule added from template.'); return redirect('calendar')
    return render(request, 'planner/schedule_form.html', {'form': form, 'page_title': 'Add schedule', 'back_url': 'calendar'})

@login_required
def shift_templates(request):
    _ensure_template(request.user)
    return render(request, 'planner/templates.html', {'templates': ShiftTemplate.objects.filter(owner=request.user)})

@login_required
def shift_template_create(request):
    form = ShiftTemplateForm(request.POST or None)
    if form.is_valid():
        item = form.save(commit=False); item.owner = request.user; item.save(); messages.success(request, 'Schedule template saved.'); return redirect('shift_templates')
    return render(request, 'planner/template_form.html', {'form': form, 'page_title': 'New schedule template', 'back_url': 'shift_templates'})

@login_required
def shift_template_delete(request, pk):
    item = get_object_or_404(ShiftTemplate, owner=request.user, pk=pk)
    if request.method == 'POST': item.delete(); messages.success(request, 'Schedule template deleted.'); return redirect('shift_templates')
    return render(request, 'planner/confirm_delete.html', {'object': item, 'back_url': 'shift_templates', 'object_type': 'schedule template'})

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, Q(created_by=request.user) | Q(assignee=request.user), pk=pk)
    form = TaskForm(request.POST or None, instance=task); form.fields['project'].queryset = _visible_projects(request.user); form.fields['assignee'].queryset = request.user.__class__.objects.filter(id=request.user.id)
    if form.is_valid(): form.save(); messages.success(request, 'Task updated.'); return redirect('tasks')
    return render(request, 'planner/form.html', {'form': form, 'page_title': 'Edit task', 'back_url': 'tasks','offline_kind':'task'})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, created_by=request.user, pk=pk)
    if request.method == 'POST': task.delete(); messages.success(request, 'Task deleted.'); return redirect('tasks')
    return render(request, 'planner/confirm_delete.html', {'object': task, 'back_url': 'tasks', 'object_type': 'task'})

@login_required
def shift_edit(request, pk):
    shift = get_object_or_404(Shift, owner=request.user, pk=pk); form = ShiftForm(request.POST or None, instance=shift, user=request.user)
    if form.is_valid(): form.save(); messages.success(request, 'Shift updated.'); return redirect('shifts')
    return render(request, 'planner/form.html', {'form': form, 'page_title': 'Edit shift', 'back_url': 'shifts'})

@login_required
def shift_delete(request, pk):
    shift = get_object_or_404(Shift, owner=request.user, pk=pk)
    if request.method == 'POST': shift.delete(); messages.success(request, 'Shift deleted.'); return redirect('shifts')
    return render(request, 'planner/confirm_delete.html', {'object': shift, 'back_url': 'shifts', 'object_type': 'shift'})

@login_required
def calendar_view(request):
    _ensure_template(request.user)
    today=timezone.localdate(); start=today-timedelta(days=today.weekday()); days=[start+timedelta(days=i) for i in range(7)]
    return render(request,'planner/calendar.html',{'days':days,'today':today,'shifts':Shift.objects.filter(owner=request.user,date__range=(days[0],days[-1])),'tasks':Task.objects.filter(Q(created_by=request.user)|Q(assignee=request.user),due_date__range=(days[0],days[-1])).distinct()})

@login_required
def notifications(request):
    return render(request,'planner/notifications.html',{'notifications':request.user.notifications.all()})

@login_required
def mark_all_read(request):
    request.user.notifications.filter(read=False).update(read=True); return redirect('notifications')

@login_required
def timeline(request):
    projects = _visible_projects(request.user).prefetch_related('tasks','milestones')
    return render(request, 'planner/timeline.html', {'projects': projects})

def service_worker(request):
    js = """const CACHE='workflow-planner-v3'; self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/offline/','/static/planner/app.css','/static/planner/theme.css','/static/planner/manifest.json','/static/planner/icon.svg'])))); self.addEventListener('activate',e=>e.waitUntil(self.clients.claim())); self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return; e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(n=>{const copy=n.clone(); caches.open(CACHE).then(c=>c.put(e.request,copy)); return n}).catch(()=>caches.match('/offline/')))}); self.addEventListener('push',e=>{const d=e.data?e.data.json():{title:'WorkFlow Planner',body:'You have a new alert.'};e.waitUntil(self.registration.showNotification(d.title||'WorkFlow Planner',{body:d.body||'',icon:'/static/planner/icon.svg',badge:'/static/planner/icon.svg',data:{url:d.url||'/schedule/'}}))}); self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.openWindow(e.notification.data?.url||'/schedule/'))});"""
    return HttpResponse(js, content_type='application/javascript')

def offline(request):
    return render(request, 'planner/offline.html')

@csrf_exempt
@login_required
@require_POST
def sync_offline(request):
    try: payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError): return HttpResponse('Invalid payload', status=400)
    created = 0
    for item in payload if isinstance(payload, list) else [payload]:
        if item.get('kind') == 'task' and item.get('title'):
            Task.objects.create(created_by=request.user, assignee=request.user, title=item['title'], description=item.get('description',''), status='TODO', priority=item.get('priority','MEDIUM')); created += 1
        elif item.get('kind') == 'note' and item.get('title'):
            Note.objects.create(owner=request.user, title=item['title'], body=item.get('body','')); created += 1
    return HttpResponse(json.dumps({'created': created}), content_type='application/json')

@login_required
def widget(request):
    """Compact, touch-friendly snapshot for a home-screen shortcut/pinned page."""
    _seed_demo(request.user)
    today = timezone.localdate()
    scope = Q(created_by=request.user) | Q(assignee=request.user)
    return render(request, 'planner/widget.html', {
        'today': today,
        'shift': Shift.objects.filter(owner=request.user, date=today).first(),
        'tasks': Task.objects.filter(scope, due_date=today).exclude(status__in=['DONE', 'CANCELLED']).distinct()[:4],
        'next_shift': Shift.objects.filter(owner=request.user, date__gt=today).first(),
        'deadline': Task.objects.filter(scope, due_date__gte=today).exclude(status__in=['DONE', 'CANCELLED']).order_by('due_date').first(),
    })

@login_required
def notes(request):
    query = request.GET.get('q', '').strip()
    items = Note.objects.filter(owner=request.user)
    if query:
        items = items.filter(Q(title__icontains=query) | Q(body__icontains=query))
    return render(request, 'planner/notes.html', {'notes': items, 'query': query})

@login_required
def note_create(request):
    form = NoteForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        note = form.save(commit=False); note.owner = request.user; note.save(); messages.success(request, 'Note saved.'); return redirect('notes')
    return render(request, 'planner/note_form.html', {'form': form, 'page_title': 'New note', 'back_url': 'notes'})

@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, owner=request.user, pk=pk)
    form = NoteForm(request.POST or None, request.FILES or None, instance=note)
    if form.is_valid(): form.save(); messages.success(request, 'Note updated.'); return redirect('notes')
    return render(request, 'planner/note_form.html', {'form': form, 'page_title': 'Edit note', 'back_url': 'notes'})

@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, owner=request.user, pk=pk)
    if request.method == 'POST': note.delete(); messages.success(request, 'Note deleted.'); return redirect('notes')
    return render(request, 'planner/confirm_delete.html', {'object': note, 'back_url': 'notes', 'object_type': 'note'})
