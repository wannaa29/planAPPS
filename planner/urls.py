from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks, name='tasks'), path('tasks/new/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/toggle/', views.task_toggle, name='task_toggle'), path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'), path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('projects/', views.projects, name='projects'), path('projects/new/', views.project_create, name='project_create'), path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'), path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('milestones/', views.milestones, name='milestones'), path('milestones/new/', views.milestone_create, name='milestone_create'), path('milestones/<int:pk>/edit/', views.milestone_edit, name='milestone_edit'), path('milestones/<int:pk>/delete/', views.milestone_delete, name='milestone_delete'),
    path('shifts/', views.shifts, name='shifts'), path('shifts/new/', views.shift_create, name='shift_create'), path('shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'), path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),
    path('calendar/', views.calendar_view, name='calendar'), path('timeline/', views.timeline, name='timeline'),
    path('notifications/', views.notifications, name='notifications'), path('notifications/read-all/', views.mark_all_read, name='mark_all_read'),
    path('service-worker.js', views.service_worker, name='service_worker'),
]
