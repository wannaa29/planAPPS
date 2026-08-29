from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Project(models.Model):
    STATUS_CHOICES = [('PLANNING','Planning'),('ACTIVE','Active'),('ON_HOLD','On hold'),('COMPLETED','Completed'),('ARCHIVED','Archived')]
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, through='ProjectMembership', related_name='planner_projects')
    color = models.CharField(max_length=7, default='#4F46E5')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return self.name
    @property
    def progress(self):
        total = self.tasks.count()
        return round(self.tasks.filter(status='DONE').count() * 100 / total) if total else 0

class ProjectMembership(models.Model):
    ROLE_CHOICES = [('OWNER','Owner'),('MANAGER','Manager'),('MEMBER','Member'),('VIEWER','Viewer')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default='MEMBER')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['project','user'], name='unique_project_member')]

class Milestone(models.Model):
    STATUS_CHOICES = [('UPCOMING','Upcoming'),('IN_PROGRESS','In progress'),('COMPLETED','Completed'),('AT_RISK','At risk'),('OVERDUE','Overdue')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')
    class Meta: ordering = ['due_date']
    @property
    def progress(self):
        total = self.tasks.count()
        return round(self.tasks.filter(status='DONE').count() * 100 / total) if total else 0
    def __str__(self): return self.name

class Task(models.Model):
    STATUS_CHOICES = [('TODO','To do'),('IN_PROGRESS','In progress'),('BLOCKED','Blocked'),('DONE','Done'),('CANCELLED','Cancelled')]
    PRIORITY_CHOICES = [('LOW','Low'),('MEDIUM','Medium'),('HIGH','High'),('URGENT','Urgent')]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(default=60)
    actual_minutes = models.PositiveIntegerField(default=0)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name='tasks')
    milestone = models.ForeignKey(Milestone, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subtasks')
    tags = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['status', '-priority', 'due_date']
        indexes = [models.Index(fields=['due_date','status']), models.Index(fields=['project','status'])]
    def __str__(self): return self.title
    @property
    def is_overdue(self): return bool(self.due_date and self.due_date < timezone.localdate() and self.status not in ('DONE','CANCELLED'))

class Shift(models.Model):
    name = models.CharField(max_length=120)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#2563EB')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts')
    @property
    def ends_next_day(self): return self.end_time <= self.start_time
    @property
    def end_datetime(self):
        end = datetime.combine(self.date, self.end_time)
        if self.ends_next_day: end += timedelta(days=1)
        return timezone.make_aware(end)
    @property
    def time_range(self): return f'{self.start_time.strftime("%H:%M")} – {self.end_time.strftime("%H:%M")}'
    class Meta: ordering = ['date','start_time']

class Notification(models.Model):
    TYPE_CHOICES = [('SHIFT_REMINDER','Shift reminder'),('TASK_REMINDER','Task reminder'),('DEADLINE_WARNING','Deadline warning'),('DEADLINE_OVERDUE','Deadline overdue'),('MILESTONE_WARNING','Milestone warning'),('MILESTONE_OVERDUE','Milestone overdue'),('PROJECT_UPDATE','Project update'),('TASK_ASSIGNED','Task assigned'),('SYSTEM','System')]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='SYSTEM')
    title = models.CharField(max_length=180)
    message = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['read','-created_at']

class ReminderPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reminder_preferences')
    shift_enabled = models.BooleanField(default=True)
    deadline_enabled = models.BooleanField(default=True)
    task_enabled = models.BooleanField(default=True)
    timezone = models.CharField(max_length=64, default='UTC')
