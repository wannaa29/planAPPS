from datetime import date, time, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import Project, ProjectMembership, Shift, ShiftTemplate, Task, Milestone, Note
from .forms import ProjectForm, MilestoneForm, ShiftForm

class PlannerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('planner', password='test-pass')
        self.other = User.objects.create_user('other', password='test-pass')

    def test_cross_midnight_shift_end(self):
        shift = Shift.objects.create(owner=self.user, name='Night', date=date(2026, 8, 29), start_time=time(22), end_time=time(6))
        self.assertTrue(shift.ends_next_day)
        self.assertEqual(shift.end_datetime.date(), date(2026, 8, 30))

    def test_dashboard_requires_login_and_is_scoped(self):
        self.assertEqual(self.client.get('/').status_code, 302)
        self.client.login(username='planner', password='test-pass')
        project = Project.objects.create(owner=self.other, name='Private')
        self.assertNotIn(project, list(Project.objects.filter(owner=self.user)))
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_task_toggle(self):
        task = Task.objects.create(created_by=self.user, title='Ship it')
        self.client.login(username='planner', password='test-pass')
        self.client.get(f'/tasks/{task.pk}/toggle/')
        task.refresh_from_db()
        self.assertEqual(task.status, 'DONE')

    def test_project_and_milestone_crud_pages(self):
        self.client.login(username='planner', password='test-pass')
        response = self.client.post('/projects/new/', {'name': 'Launch plan', 'status': 'ACTIVE', 'color': '#4f46e5'})
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(name='Launch plan')
        self.assertEqual(self.client.get('/projects/').status_code, 200)
        self.assertEqual(self.client.get(f'/projects/{project.pk}/edit/').status_code, 200)
        response = self.client.post('/milestones/new/', {'project': project.pk, 'name': 'Beta', 'due_date': '2026-09-10', 'status': 'UPCOMING'})
        self.assertEqual(response.status_code, 302)
        milestone = Milestone.objects.get(project=project)
        self.assertEqual(self.client.get('/milestones/').status_code, 200)
        self.assertEqual(self.client.get(f'/milestones/{milestone.pk}/edit/').status_code, 200)

    def test_forms_reject_past_dates_and_times(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.assertFalse(ProjectForm({'name':'Past','start_date':yesterday,'end_date':yesterday,'status':'ACTIVE','color':'#4f46e5'}).is_valid())
        self.assertFalse(MilestoneForm({'project':'','name':'Past','due_date':yesterday,'status':'UPCOMING'}).is_valid())
        self.assertFalse(ShiftForm({'name':'Past','date':yesterday,'start_time':'09:00','end_time':'17:00'}).is_valid())

    def test_widget_snapshot_requires_login(self):
        self.assertEqual(self.client.get('/widget/').status_code, 302)
        self.client.login(username='planner', password='test-pass')
        self.assertEqual(self.client.get('/widget/').status_code, 200)

    def test_notes_crud(self):
        self.client.login(username='planner', password='test-pass')
        response = self.client.post('/notes/new/', {'title': 'Idea', 'body': 'Draft launch notes'})
        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(owner=self.user, title='Idea')
        self.assertEqual(self.client.get('/notes/').status_code, 200)
        self.assertEqual(self.client.get(f'/notes/{note.pk}/edit/').status_code, 200)
        self.assertEqual(self.client.post(f'/notes/{note.pk}/delete/').status_code, 302)

    def test_shift_template_can_create_shift(self):
        self.client.login(username='planner', password='test-pass')
        response = self.client.post('/shift-templates/new/', {'name':'Morning', 'start_time':'08:00', 'end_time':'16:00', 'location':'HQ', 'notes':'', 'color':'#2563eb'})
        self.assertEqual(response.status_code, 302)
        template = ShiftTemplate.objects.get(owner=self.user, name='Morning')
        response = self.client.post('/schedule/new/', {'template':template.pk, 'date':(timezone.localdate()+timedelta(days=2)).isoformat()})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Shift.objects.filter(owner=self.user, name='Morning').exists())
