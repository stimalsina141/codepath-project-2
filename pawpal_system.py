"""PawPal+ logic layer.

Backend classes for the pet care planner. This module holds all scheduling
logic so that `app.py` stays a thin Streamlit UI on top of it.

Phase 3: class skeletons only. Every method raises NotImplementedError until
the behavior is filled in during Phase 4.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single unit of pet care, e.g. a 30-minute morning walk."""

    task_id: str
    title: str
    duration_minutes: int
    priority: str
    category: str = "general"
    preferred_time: str | None = None
    recurrence: str = "daily"
    completed: bool = False

    def mark_complete(self) -> None:
        """Flag this task as done for the day."""
        raise NotImplementedError

    def priority_score(self) -> int:
        """Return the priority as a sortable number (higher = more urgent)."""
        raise NotImplementedError

    def is_due_today(self, day: str) -> bool:
        """Return True if this task's recurrence means it runs on `day`."""
        raise NotImplementedError

    def fits_in(self, minutes_left: int) -> bool:
        """Return True if this task can be completed within the remaining budget."""
        raise NotImplementedError


@dataclass
class Pet:
    """An animal in the owner's care, along with its own task list."""

    pet_id: str
    name: str
    species: str
    breed: str = ""
    age: int = 0
    weight_lbs: float = 0.0
    energy_level: str = "medium"
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        raise NotImplementedError

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by id. Returns True if one was removed."""
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        """Return every task for this pet."""
        raise NotImplementedError

    def get_pending_tasks(self) -> list[Task]:
        """Return only the tasks that have not been completed yet."""
        raise NotImplementedError

    def total_duration(self) -> int:
        """Return the combined minutes of all pending tasks."""
        raise NotImplementedError


@dataclass
class Owner:
    """The person using PawPal+, plus the time budget that constrains a day."""

    owner_id: str
    name: str
    email: str = ""
    available_minutes: int = 60
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet_id: str) -> bool:
        """Remove a pet by id. Returns True if one was removed."""
        raise NotImplementedError

    def get_pet(self, pet_id: str) -> Pet | None:
        """Look up a pet by id, or None if there is no match."""
        raise NotImplementedError

    def total_task_count(self) -> int:
        """Return the number of tasks across all of this owner's pets."""
        raise NotImplementedError


class Scheduler:
    """Builds a daily plan from an owner's tasks and time budget.

    Keeps the skipped tasks and the reasoning alongside the plan so the UI can
    explain why each task was chosen and when it happens.
    """

    def __init__(
        self,
        owner: Owner,
        available_minutes: int | None = None,
        start_time: str = "08:00",
    ) -> None:
        self.owner = owner
        self.available_minutes = (
            available_minutes if available_minutes is not None else owner.available_minutes
        )
        self.start_time = start_time
        self.planned: list[Task] = []
        self.skipped: list[Task] = []
        self.reasons: list[str] = []

    def generate_plan(self) -> list[Task]:
        """Run the full pipeline: sort, filter by budget, assign time slots."""
        raise NotImplementedError

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks so the most important ones are scheduled first."""
        raise NotImplementedError

    def filter_by_budget(self, tasks: list[Task]) -> list[Task]:
        """Keep tasks that fit the time budget; record the rest as skipped."""
        raise NotImplementedError

    def assign_time_slots(self, tasks: list[Task]) -> list[Task]:
        """Walk the clock forward from start_time, stamping each task."""
        raise NotImplementedError

    def explain_plan(self) -> list[str]:
        """Return a human-readable line for each scheduling decision."""
        raise NotImplementedError

    def get_skipped_tasks(self) -> list[Task]:
        """Return the tasks that did not make it into the plan."""
        raise NotImplementedError

    def reset(self) -> None:
        """Clear the previous plan so a new one can be generated."""
        raise NotImplementedError
