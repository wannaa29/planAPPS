# Product Requirements Document
# WorkFlow Planner

## 1. Product Overview

WorkFlow Planner is a web-based productivity and work planning application.

The application combines:

- Personal productivity
- Work shift management
- Task management
- Project management
- Calendar planning
- Milestones
- Deadlines
- Reminders
- Notifications
- Team collaboration

The product helps users organize their work and personal project schedules without needing multiple applications.

---

# 2. Problem Statement

Users who work with shifts and projects often manage schedules across multiple tools.

For example:

- Work shifts are stored in a calendar.
- Tasks are stored in a Todo application.
- Project deadlines are stored elsewhere.
- Reminders are handled by a phone.
- Team projects are managed in another application.

This creates fragmented planning.

Users need a single system that connects:

`Shift → Available Time → Task → Project → Milestone → Deadline → Reminder`

---

# 3. Product Vision

Create a centralized work planning system that helps users understand:

> What am I doing today, when am I doing it, and what needs my attention next?

---

# 4. Target Users

## Primary User

Individual users who:

- Work rotating shifts
- Have personal projects
- Manage multiple deadlines
- Need reminders
- Want structured daily planning

## Secondary User

Small teams that:

- Manage projects
- Assign tasks
- Track deadlines
- Need milestone tracking

---

# 5. Goals

## Product Goals

- Centralize schedules and projects.
- Reduce missed deadlines.
- Make daily planning easier.
- Provide clear visibility into workload.
- Help users plan around work shifts.
- Provide actionable reminders.

## MVP Goals

Users should be able to:

1. Create an account.
2. Create work shifts.
3. Create tasks.
4. Create projects.
5. Create milestones.
6. View everything in a calendar.
7. Configure reminders.
8. Receive notifications.
9. Track project progress.

---

# 6. Non-Goals for MVP

Do not initially build:

- Full AI assistant
- Advanced AI scheduling
- Video meetings
- Chat system
- Complex document editor
- Payroll
- Employee attendance
- HR management
- Invoicing

These may be considered later.

---

# 7. Core User Journey

## New User

Register
↓
Configure timezone/preferences
↓
Create work schedule
↓
Create project
↓
Create milestones
↓
Create tasks
↓
Configure reminders
↓
View dashboard
↓
Receive notifications

---

# 8. Functional Requirements

## 8.1 Authentication

Users can:

- Register
- Login
- Logout
- Reset password
- Update profile

---

## 8.2 Dashboard

Dashboard displays:

- Current date
- Current shift
- Next shift
- Today's tasks
- Overdue tasks
- Upcoming deadlines
- Upcoming milestones
- Project progress
- Notifications

---

# 9. Task Requirements

A task contains:

- Title
- Description
- Status
- Priority
- Start date
- Due date
- Estimated duration
- Project
- Milestone
- Assignee
- Tags
- Parent task
- Dependencies

Users can:

- Create
- Read
- Update
- Delete
- Complete
- Assign
- Filter
- Search
- Sort

---

# 10. Project Requirements

Project contains:

- Name
- Description
- Status
- Start date
- End date
- Owner
- Members

Users can:

- Create project
- Edit project
- Archive project
- Add members
- Remove members
- View project progress

---

# 11. Milestone Requirements

Milestone contains:

- Name
- Description
- Project
- Due date
- Status

The system calculates milestone progress from related tasks when appropriate.

---

# 12. Shift Requirements

Shift contains:

- Name
- Date
- Start time
- End time
- Location
- Notes
- Color

The system must support:

- Single shifts
- Repeating shifts
- Custom schedules
- Overnight shifts

Example:

22:00 → 06:00

must be treated as an overnight shift.

---

# 13. Calendar Requirements

Calendar displays:

- Shifts
- Tasks
- Deadlines
- Milestones
- Events

Views:

- Month
- Week
- Day

---

# 14. Reminder Requirements

Reminder types:

### Shift

- 24 hours before
- 2 hours before
- 30 minutes before

### Deadline

- 7 days before
- 3 days before
- 1 day before
- 3 hours before
- 30 minutes before

### Task

Custom reminder.

Users can enable/disable reminder types.

---

# 15. Notification Requirements

Notifications are generated for:

- Upcoming shifts
- Upcoming deadlines
- Overdue tasks
- Overdue milestones
- Task assignments
- Project updates
- Schedule conflicts

Users can:

- Mark as read
- Mark all as read
- Delete notifications
- Open related object

---

# 16. Alert Rules

## Deadline Warning

If:

`deadline - current_time <= warning_threshold`

create notification.

## Overdue

If:

`deadline < current_time`

and task is not completed:

mark task as overdue.

## Shift Reminder

If:

`shift_start - current_time <= configured_reminder_time`

create reminder.

## Milestone Risk

A milestone becomes AT_RISK when:

- Due date is approaching
- Required tasks remain incomplete
- Project progress is insufficient

---

# 17. Team Requirements

Project roles:

| Role | Permissions |
|------|-------------|
| OWNER | Full control |
| MANAGER | Manage project and members |
| MEMBER | Manage assigned tasks |
| VIEWER | Read only |

All permissions must be enforced server-side.

---

# 18. Smart Scheduling — Future

The scheduler will eventually calculate:

`Available Time - Shifts - Existing Events`

and use the remaining time for tasks.

Task ranking should consider:

- Deadline
- Priority
- Estimated duration
- Dependencies
- Project importance

Output:

A recommended schedule.

---

# 19. Success Metrics

Possible metrics:

- Daily active users
- Tasks completed
- Overdue tasks
- Reminder interaction rate
- Projects completed
- Calendar usage
- Number of missed deadlines
- Weekly retention

---

# 20. MVP Acceptance Criteria

The MVP is considered complete when:

- Users can register/login.
- Users can create shifts.
- Users can create projects.
- Users can create milestones.
- Users can create tasks.
- Tasks can be assigned to projects.
- Calendar displays schedules.
- Deadlines are visible.
- Reminder preferences work.
- Notifications are generated.
- Overdue tasks are detected.
- Project progress is displayed.
- Permissions are enforced.
- Timezones work correctly.
- Core functionality has automated tests.
