"""PawPal+ logic layer.

Backend classes for the pet care planner. This module holds all scheduling
logic so that `app.py` stays a thin Streamlit UI on top of it.

Times are handled as minutes since midnight (an int) wherever the scheduler
does arithmetic, and converted to a "HH:MM" string only for display.
"""

from dataclasses import dataclass, field

# Maps a priority label to a sortable number. Higher wins.
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

MINUTES_PER_DAY = 24 * 60


def parse_time(text: str) -> int:
    """Convert a "HH:MM" string into minutes since midnight."""
    try:
        hours, minutes = text.strip().split(":")
        total = int(hours) * 60 + int(minutes)
    except (AttributeError, ValueError):
        raise ValueError(f"expected a time like '08:30', got {text!r}")
    if not 0 <= total < MINUTES_PER_DAY:
        raise ValueError(f"time out of range: {text!r}")
    return total


def format_time(minutes: int) -> str:
    """Convert minutes since midnight into a "HH:MM" string.

    Wraps around midnight so a plan running past 24:00 shows 00:30 rather
    than 24:30.
    """
    minutes %= MINUTES_PER_DAY
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """A single unit of pet care, e.g. a 30-minute morning walk.

    The first block of fields is input: what the owner tells us about the task.
    The last block is output: what the scheduler fills in when it builds a plan.
    """

    task_id: str
    title: str
    duration_minutes: int
    priority: str
    pet_id: str = ""
    category: str = "general"
    preferred_time: str | None = None
    recurrence: str = "daily"
    days: list[str] = field(default_factory=list)
    completed: bool = False

    # Set by the scheduler, cleared by Scheduler.reset().
    scheduled_minutes: int | None = None
    reason: str = ""

    def mark_complete(self) -> None:
        """Flag this task as done for the day."""
        self.completed = True

    def reopen(self) -> None:
        """Flag this task as not done after all, so it can be planned again."""
        self.completed = False

    def priority_score(self) -> int:
        """Return the priority as a sortable number (higher = more urgent).

        An unrecognized priority scores 0, so it sorts below everything real
        instead of crashing the plan.
        """
        return PRIORITY_ORDER.get(self.priority.strip().lower(), 0)

    def is_due_today(self, day: str) -> bool:
        """Return True if this task's recurrence means it runs on `day`.

        A "daily" task is always due. A "weekly" task is due only on the days
        listed in `self.days`; an empty list means no day restriction.
        """
        if self.recurrence.strip().lower() != "weekly":
            return True
        if not self.days:
            return True
        return day.strip().lower() in [d.strip().lower() for d in self.days]

    def fits_in(self, minutes_left: int) -> bool:
        """Return True if this task can be completed within the remaining budget."""
        return self.duration_minutes <= minutes_left

    def scheduled_time(self) -> str:
        """Return the assigned slot as "HH:MM", or "" if not scheduled."""
        if self.scheduled_minutes is None:
            return ""
        return format_time(self.scheduled_minutes)

    def clear_schedule(self) -> None:
        """Wipe the scheduler's output fields so this task can be replanned."""
        self.scheduled_minutes = None
        self.reason = ""


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
        """Attach a task to this pet and stamp the task's pet_id."""
        task.pet_id = self.pet_id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by id. Returns True if one was removed."""
        for index, task in enumerate(self.tasks):
            if task.task_id == task_id:
                del self.tasks[index]
                return True
        return False

    def get_tasks(self) -> list[Task]:
        """Return every task for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only the tasks that have not been completed yet."""
        return [task for task in self.tasks if not task.completed]

    def total_duration(self) -> int:
        """Return the combined minutes of all pending tasks."""
        return sum(task.duration_minutes for task in self.get_pending_tasks())


@dataclass
class Owner:
    """The person using PawPal+, plus the time budget that constrains a day."""

    owner_id: str
    name: str
    email: str = ""
    available_minutes: int = 60
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet to this owner, replacing any pet with the same id."""
        self.remove_pet(pet.pet_id)
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> bool:
        """Remove a pet by id. Returns True if one was removed."""
        for index, pet in enumerate(self.pets):
            if pet.pet_id == pet_id:
                del self.pets[index]
                return True
        return False

    def get_pet(self, pet_id: str) -> Pet | None:
        """Look up a pet by id, or None if there is no match."""
        for pet in self.pets:
            if pet.pet_id == pet_id:
                return pet
        return None

    def total_task_count(self) -> int:
        """Return the number of tasks across all of this owner's pets."""
        return sum(len(pet.tasks) for pet in self.pets)


class Scheduler:
    """Builds a daily plan from an owner's tasks and time budget.

    Each task carries its own start time and the reason it was chosen or
    skipped, so the UI can explain the plan instead of just listing it.
    """

    def __init__(
        self,
        owner: Owner,
        available_minutes: int | None = None,
        start_time: str = "08:00",
    ) -> None:
        """Set up a planner for one owner, falling back to their own time budget."""
        self.owner = owner
        self.available_minutes = (
            available_minutes if available_minutes is not None else owner.available_minutes
        )
        self.start_time = start_time
        self.planned: list[Task] = []
        self.skipped: list[Task] = []

    def collect_tasks(self, day: str = "daily") -> list[Task]:
        """Gather every pending, due task across all of the owner's pets."""
        due = []
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                if task.is_due_today(day):
                    due.append(task)
        return due

    def generate_plan(self, day: str = "daily") -> list[Task]:
        """Run the full pipeline: collect, sort, filter by budget, assign slots."""
        self.reset()
        tasks = self.sort_tasks(self.collect_tasks(day))
        kept = self.filter_by_budget(tasks)
        self.planned = self.assign_time_slots(kept)
        return self.planned

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks so the most important ones are scheduled first.

        Highest priority first, then shortest first within the same priority,
        so a tight budget fits as many tasks as it can. Title breaks ties to
        keep the order predictable.
        """
        return sorted(
            tasks,
            key=lambda task: (-task.priority_score(), task.duration_minutes, task.title),
        )

    def filter_by_budget(self, tasks: list[Task]) -> list[Task]:
        """Keep tasks that fit the time budget; record the rest as skipped.

        Sets each task's `reason` to explain why it was kept or dropped. A task
        that does not fit does not stop the walk: a shorter, lower-priority task
        further down the list can still use the leftover minutes.
        """
        remaining = self.available_minutes
        kept: list[Task] = []
        for task in tasks:
            if task.fits_in(remaining):
                remaining -= task.duration_minutes
                task.reason = f"{remaining} min of budget left"
                kept.append(task)
            else:
                task.reason = (
                    f"needs {task.duration_minutes} min, only {remaining} min left"
                )
                self.skipped.append(task)
        return kept

    def assign_time_slots(self, tasks: list[Task]) -> list[Task]:
        """Walk the clock forward from start_time, stamping each task.

        Works in minutes since midnight, so each slot is the previous start
        plus that task's duration. A task with a preferred_time still to come
        pushes the clock forward to meet it.
        """
        cursor = parse_time(self.start_time)
        for task in tasks:
            if task.preferred_time:
                wanted = parse_time(task.preferred_time)
                if wanted > cursor:
                    cursor = wanted
            task.scheduled_minutes = cursor
            cursor += task.duration_minutes
        return tasks

    def explain_plan(self) -> list[str]:
        """Return a human-readable line for each scheduled and skipped task.

        Used by the Streamlit UI, where there are no table columns to carry the
        priority, so each line spells it out.
        """
        lines = []
        for task in self.planned:
            pet = self.pet_for(task)
            who = f" for {pet.name}" if pet else ""
            lines.append(
                f"{task.scheduled_time()} — {task.title}{who} "
                f"({task.duration_minutes} min, {task.priority} priority) "
                f"— {task.reason}"
            )
        for task in self.skipped:
            pet = self.pet_for(task)
            who = f" for {pet.name}" if pet else ""
            lines.append(
                f"skipped — {task.title}{who} "
                f"({task.duration_minutes} min, {task.priority} priority) "
                f"— {task.reason}"
            )
        return lines

    def get_skipped_tasks(self) -> list[Task]:
        """Return the tasks that did not make it into the plan."""
        return list(self.skipped)

    def pet_for(self, task: Task) -> Pet | None:
        """Find the pet a scheduled task belongs to, for display."""
        return self.owner.get_pet(task.pet_id)

    def reset(self) -> None:
        """Clear the previous plan, including the output fields on every task."""
        self.planned = []
        self.skipped = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                task.clear_schedule()
