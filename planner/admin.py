from django.contrib import admin
from .models import Project, ProjectMembership, Milestone, Task, Shift, Notification, ReminderPreference

admin.site.register([Project, ProjectMembership, Milestone, Task, Shift, Notification, ReminderPreference])
