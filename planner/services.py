from dataclasses import dataclass
from datetime import date
from typing import Iterable
from .models import Task, Shift

@dataclass
class ScheduleBlock:
    start: object
    end: object
    task: Task

class SchedulingService:
    """Small seam for the future smart scheduler; MVP returns prioritized work."""
    def recommend(self, tasks: Iterable[Task], shifts: Iterable[Shift], day: date):
        return sorted((task for task in tasks if task.status not in ('DONE','CANCELLED')), key=lambda t: ({'URGENT':0,'HIGH':1,'MEDIUM':2,'LOW':3}.get(t.priority,2), t.due_date or date.max))
