from celery import shared_task
from django.utils import timezone
from .models import Task, Notification

@shared_task
def detect_overdue_tasks():
    today = timezone.localdate()
    for task in Task.objects.filter(due_date__lt=today).exclude(status__in=['DONE','CANCELLED']):
        recipient = task.assignee or task.created_by
        if not Notification.objects.filter(recipient=recipient, type='DEADLINE_OVERDUE', title=task.title).exists():
            Notification.objects.create(recipient=recipient, type='DEADLINE_OVERDUE', title=task.title, message='This task is overdue.')
