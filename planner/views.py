from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.utils import timezone
from .forms import TaskForm, ProjectForm, MilestoneForm, ShiftForm
from .models import Task, Project, ProjectMembership, Milestone, Shift, Notification, ReminderPreference

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
    Shift.objects.create(owner=user, name='Morning shift', date=today, start_time='08:00', end_time='16:00', location='HQ · Floor 2')
    Shift.objects.create(owner=user, name='Morning shift', date=today+timedelta(days=1), start_time='08:00', end_time='16:00', location='HQ · Floor 2')
    Notification.objects.create(recipient=user, type='DEADLINE_WARNING', title='Public launch is coming up', message='Your milestone is due in 12 days.')

@login_required
def dashboard(request):
    _seed_demo(request.user)
    today = timezone.localdate(); projects = _visible_projects(request.user); scope = Q(created_by=request.user) | Q(assignee=request.user)
    todays_tasks = Task.objects.filter(scope, due_date=today).distinct()
    overdue = Task.objects.filter(scope, due_date__lt=today).exclude(status__in=['DONE','CANCELLED']).distinct()
    shifts_today = Shift.objects.filter(owner=request.user, date=today)
    upcoming_shifts = Shift.objects.filter(owner=request.user, date__gt=today)[:3]
    deadlines = Task.objects.filter(scope, due_date__gte=today, due_date__lte=today+timedelta(days=14)).exclude(status__in=['DONE','CANCELLED']).order_by('due_date')[:4]
    milestones_upcoming = Milestone.objects.filter(project__in=projects, due_date__gte=today).order_by('due_date')[:3]
    return render(request, 'planner/dashboard.html', {'today':today,'todays_tasks':todays_tasks,'overdue':overdue,'shifts_today':shifts_today,'upcoming_shifts':upcoming_shifts,'deadlines':deadlines,'milestones':milestones_upcoming,'projects':projects[:4],'notifications':request.user.notifications.all()[:4],'unread_count':request.user.notifications.filter(read=False).count()})

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
    return render(request, 'planner/form.html', {'form':form,'page_title':'New task','back_url':'tasks'})

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
    return render(request,'planner/list.html',{'page_title':'Shifts','subtitle':'Plan around the hours you are committed to.','items':Shift.objects.filter(owner=request.user),'item_type':'shift'})

@login_required
def shift_create(request):
    form=ShiftForm(request.POST or None)
    if form.is_valid(): shift=form.save(commit=False); shift.owner=request.user; shift.save(); messages.success(request,'Shift scheduled.'); return redirect('shifts')
    return render(request,'planner/form.html',{'form':form,'page_title':'New shift','back_url':'shifts'})

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, Q(created_by=request.user) | Q(assignee=request.user), pk=pk)
    form = TaskForm(request.POST or None, instance=task); form.fields['project'].queryset = _visible_projects(request.user); form.fields['assignee'].queryset = request.user.__class__.objects.filter(id=request.user.id)
    if form.is_valid(): form.save(); messages.success(request, 'Task updated.'); return redirect('tasks')
    return render(request, 'planner/form.html', {'form': form, 'page_title': 'Edit task', 'back_url': 'tasks'})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, created_by=request.user, pk=pk)
    if request.method == 'POST': task.delete(); messages.success(request, 'Task deleted.'); return redirect('tasks')
    return render(request, 'planner/confirm_delete.html', {'object': task, 'back_url': 'tasks', 'object_type': 'task'})

@login_required
def shift_edit(request, pk):
    shift = get_object_or_404(Shift, owner=request.user, pk=pk); form = ShiftForm(request.POST or None, instance=shift)
    if form.is_valid(): form.save(); messages.success(request, 'Shift updated.'); return redirect('shifts')
    return render(request, 'planner/form.html', {'form': form, 'page_title': 'Edit shift', 'back_url': 'shifts'})

@login_required
def shift_delete(request, pk):
    shift = get_object_or_404(Shift, owner=request.user, pk=pk)
    if request.method == 'POST': shift.delete(); messages.success(request, 'Shift deleted.'); return redirect('shifts')
    return render(request, 'planner/confirm_delete.html', {'object': shift, 'back_url': 'shifts', 'object_type': 'shift'})

@login_required
def calendar_view(request):
    today=timezone.localdate(); start=today-timedelta(days=today.weekday()); days=[start+timedelta(days=i) for i in range(7)]
    return render(request,'planner/calendar.html',{'days':days,'shifts':Shift.objects.filter(owner=request.user,date__range=(days[0],days[-1])),'tasks':Task.objects.filter(Q(created_by=request.user)|Q(assignee=request.user),due_date__range=(days[0],days[-1])).distinct()})

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
    js = """const CACHE='workflow-planner-v1'; self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/static/planner/app.css','/static/planner/manifest.json','/static/planner/icon.svg'])))); self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return; e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(n=>{const copy=n.clone(); caches.open(CACHE).then(c=>c.put(e.request,copy)); return n}).catch(()=>caches.match('/static/planner/app.css')))});"""
    return HttpResponse(js, content_type='application/javascript')
