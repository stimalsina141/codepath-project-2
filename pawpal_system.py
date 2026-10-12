"""PawPal+ logic layer.

Backend classes for the pet care planner. This module holds all scheduling
logic so that `app.py` stays a thin Streamlit UI on top of it.

Times are handled as minutes since midnight (an int) wherever the scheduler
does arithmetic, and converted to a "HH:MM" string only for display.
"""

from dataclasses import dataclass, field, replace
from itertools import combinations
from datetime import date, timedelta

# Maps a priority label to a sortable number. Higher wins.
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

MINUTES_PER_DAY = 24 * 60

# How far apart repeat occurrences of a recurring task fall. "once" has no
# entry, so completing a one-off task does not create another.
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}

# A task that starts more than this many minutes after its preferred time is
# reported as running late.
LATE_TOLERANCE_MINUTES = 15


def parse_time(text: str) -> int:
    """Convert a "HH:MM" string into minutes since midnight."""
    try:
        hours, minutes = text.strip().split(":")
        hour_value, minute_value = int(hours), int(minutes)
    except (AttributeError, ValueError):
        raise ValueError(f"expected a time like '08:30', got {text!r}")
    # Check the minutes on their own: "08:70" would otherwise slide through as
    # 09:10 rather than being rejected as the typo it is.
    if not 0 <= minute_value < 60:
        raise ValueError(f"minutes out of range: {text!r}")
    total = hour_value * 60 + minute_value
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
    due_date: date | None = None
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

    def next_occurrence(self, completed_on: date) -> "Task | None":
        """Return a fresh copy of this task for its next due date, or None.

        A daily task comes back the next day and a weekly one a week later.
        Anything else (e.g. "once") does not repeat. The copy gets a new id
        derived from the due date so it never collides with the original.
        """
        step = RECURRENCE_STEP.get(self.recurrence.strip().lower())
        if step is None:
            return None
        next_due = completed_on + step
        base_id = self.task_id.split("@")[0]
        return replace(
            self,
            task_id=f"{base_id}@{next_due.isoformat()}",
            due_date=next_due,
            completed=False,
            scheduled_minutes=None,
            reason="",
        )

    def preferred_minutes(self) -> int | None:
        """Return preferred_time as minutes since midnight, or None if unset."""
        if not self.preferred_time:
            return None
        return parse_time(self.preferred_time)

    def is_due_today(self, day: str, on: date | None = None) -> bool:
        """Return True if this task runs on weekday `day` (and date `on`, if given).

        A task with a due_date later than `on` is not due yet. Otherwise a
        "daily" task is always due, and a "weekly" task is due only on the days
        listed in `self.days`; an empty list means no day restriction.
        """
        if on is not None and self.due_date is not None and self.due_date > on:
            return False
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

    def sort_minutes(self) -> int | None:
        """Return the minute this task sits at for ordering, or None if untimed.

        Its assigned slot if it has one, otherwise its preferred time. The
        assigned slot is deliberately left unwrapped: a plan running past
        midnight keeps climbing (1410, 1440, 1470), so a task at 00:30 still
        sorts after one at 23:00. format_time() wraps it only for display.
        """
        if self.scheduled_minutes is not None:
            return self.scheduled_minutes
        return self.preferred_minutes()

    def time_string(self) -> str:
        """Return the assigned slot, else the preferred time, as zero-padded "HH:MM".

        preferred_time is re-formatted so a hand-typed "8:00" becomes "08:00"
        and still sorts correctly as a string. Returns "" if neither is set.
        """
        if self.scheduled_minutes is not None:
            return self.scheduled_time()
        if self.preferred_time:
            return format_time(self.preferred_minutes())
        return ""

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

    def complete_task(self, task_id: str, on: date | None = None) -> Task | None:
        """Mark a task done and, if it recurs, queue its next occurrence.

        Returns the newly created follow-up task, or None if the task was not
        found or does not repeat.
        """
        on = on or date.today()
        for task in self.tasks:
            if task.task_id == task_id:
                task.mark_complete()
                follow_up = task.next_occurrence(on)
                if follow_up is not None:
                    self.add_task(follow_up)
                return follow_up
        return None

    def reopen_task(self, task_id: str) -> None:
        """Undo complete_task: reopen the task and drop the copy it queued.

        The queued copy is found by its id (same base id before the "@") and
        a later due date. Only pending copies are removed, so finished history
        and the reopened task itself are kept.
        """
        for task in self.tasks:
            if task.task_id == task_id:
                task.reopen()
                prefix = task_id.split("@")[0] + "@"

                def is_queued_copy(other: Task) -> bool:
                    """True if `other` is a pending future copy of `task`."""
                    return (
                        other is not task
                        and not other.completed
                        and other.task_id.startswith(prefix)
                        and (task.due_date is None or (other.due_date or task.due_date) > task.due_date)
                    )

                self.tasks = [t for t in self.tasks if not is_queued_copy(t)]
                return

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
        self.conflicts: list[str] = []

    def collect_tasks(self, day: str, on: date | None = None) -> list[Task]:
        """Gather every pending, due task across all of the owner's pets."""
        due = []
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                if task.is_due_today(day, on):
                    due.append(task)
        return due

    def filter_tasks(
        self,
        pet_id: str | None = None,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return the owner's tasks, narrowed by pet and/or completion status.

        The pet can be picked by id or by name (case-insensitive). Leaving a
        filter as None means "don't filter on this", so filter_tasks() with no
        arguments returns every task.
        """
        wanted_name = pet_name.strip().lower() if pet_name else None
        return [
            task
            for pet in self.owner.pets
            if (pet_id is None or pet.pet_id == pet_id)
            and (wanted_name is None or pet.name.lower() == wanted_name)
            for task in pet.tasks
            if completed is None or task.completed == completed
        ]

    def generate_plan(self, day: str | None = None, on: date | None = None) -> list[Task]:
        """Run the full pipeline and return the day's plan in time order.

        Steps: collect the pending tasks due on `day`/`on`, sort them by
        priority, keep the ones that fit the time budget, lay them out on the
        clock, then check the result for time conflicts. Skipped tasks and
        conflict warnings are kept on the scheduler (get_skipped_tasks,
        get_conflicts).

        `on` defaults to today, and `day` defaults to `on`'s weekday. Passing
        `day` explicitly lets the UI plan for a different weekday.
        """
        self.reset()
        on = on or date.today()
        day = day or on.strftime("%A").lower()
        tasks = self.sort_tasks(self.collect_tasks(day, on))
        kept = self.filter_by_budget(tasks)
        self.planned = self.assign_time_slots(kept)
        self.conflicts = self.detect_conflicts(self.planned)
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

        Sets each skipped task's `reason` to explain why it was dropped (kept
        tasks get theirs when they are given a time slot). A task
        that does not fit does not stop the walk: a shorter, lower-priority task
        further down the list can still use the leftover minutes.
        """
        remaining = self.available_minutes
        kept: list[Task] = []
        for task in tasks:
            if task.fits_in(remaining):
                remaining -= task.duration_minutes
                kept.append(task)
            else:
                task.reason = (
                    f"needs {task.duration_minutes} min, only {remaining} min left"
                )
                self.skipped.append(task)
        return kept

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by clock time.

        The key is Task.sort_minutes() — the assigned slot if there is one,
        else the preferred time — as a number rather than a "HH:MM" string.
        Minutes are used because a plan that runs past midnight wraps its
        displayed time back to 00:30, and sorting on that string would put
        the task first instead of last. Untimed tasks sort after every timed
        one; priority then title break ties.
        """

        def order(task: Task) -> tuple[float, int, str]:
            """Sort key: when it happens, then priority, then title."""
            minutes = task.sort_minutes()
            return (
                float("inf") if minutes is None else minutes,
                -task.priority_score(),
                task.title,
            )

        return sorted(tasks, key=order)

    def assign_time_slots(self, tasks: list[Task]) -> list[Task]:
        """Lay tasks out on the clock, returning them in time order.

        Tasks with a preferred_time are anchors, placed in time order at that
        time (or as soon after as the clock allows). Flexible tasks keep the
        priority order they arrive in and fill the gaps: before each anchor,
        any flexible task that finishes in time is slotted into the gap, and
        whatever is left runs after the last anchor.
        """
        anchors = self.sort_by_time([t for t in tasks if t.preferred_time])
        flexible = [t for t in tasks if not t.preferred_time]
        cursor = parse_time(self.start_time)

        for anchor in anchors:
            wanted = anchor.preferred_minutes()
            for task in list(flexible):
                if cursor + task.duration_minutes <= wanted:
                    task.scheduled_minutes = cursor
                    task.reason = f"flexible, fills the gap before {format_time(anchor.preferred_minutes())}"
                    cursor += task.duration_minutes
                    flexible.remove(task)
            anchor.scheduled_minutes = max(cursor, wanted)
            delay = anchor.scheduled_minutes - wanted
            if delay:
                anchor.reason = f"wanted {format_time(anchor.preferred_minutes())}, pushed back {delay} min"
            else:
                anchor.reason = "at its preferred time"
            cursor = anchor.scheduled_minutes + anchor.duration_minutes

        for task in flexible:
            task.scheduled_minutes = cursor
            task.reason = f"flexible, {task.priority} priority"
            cursor += task.duration_minutes

        return self.sort_by_time(tasks)

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning for each clash between requested times.

        Lightweight by design: problems come back as messages, never as
        exceptions, so the plan still shows. Three kinds are reported:
          * same time: two tasks want exactly the same start time.
          * overlap: one task's preferred window starts before another's
            has ended, so one of them had to move.
          * late: a task ended up starting more than LATE_TOLERANCE_MINUTES
            after its preferred time.

        Clashes are checked for every pair of timed tasks, whether they belong
        to the same pet (one pet can't do two things at once) or to different
        pets (the owner can't be in two places at once). A day holds only a
        handful of tasks, so comparing all pairs is cheap and misses nothing.
        """
        warnings: list[str] = []

        timed = sorted(
            (t for t in tasks if t.preferred_time),
            key=lambda t: (t.preferred_minutes(), -t.priority_score(), t.title),
        )
        for first, second in combinations(timed, 2):
            first_start, second_start = first.preferred_minutes(), second.preferred_minutes()
            first_end = first_start + first.duration_minutes
            if second_start >= first_end:
                continue
            who = "same pet" if first.pet_id == second.pet_id else "different pets"
            if first_start == second_start:
                warnings.append(
                    f"Same time: {self._label(first)} and {self._label(second)} "
                    f"both want {format_time(first_start)} ({who})"
                )
            else:
                warnings.append(
                    f"Overlap: {self._label(second)} wants {format_time(second_start)}, but "
                    f"{self._label(first)} runs {format_time(first_start)}–{format_time(first_end)} ({who})"
                )

        for task in tasks:
            wanted = task.preferred_minutes()
            if wanted is None or task.scheduled_minutes is None:
                continue
            delay = task.scheduled_minutes - wanted
            if delay > LATE_TOLERANCE_MINUTES:
                warnings.append(
                    f"Late: {self._label(task)} wanted {format_time(task.preferred_minutes())} but starts at "
                    f"{task.scheduled_time()} ({delay} min late)"
                )

        return warnings

    def _label(self, task: Task) -> str:
        """Return "Mochi's 'Walk'" style text naming a task and its pet."""
        pet = self.pet_for(task)
        return f"{pet.name}'s '{task.title}'" if pet else f"'{task.title}'"

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

    def mark_task_complete(self, task: Task, on: date | None = None) -> Task | None:
        """Mark a task done and, if it is daily or weekly, queue its next occurrence.

        The caller only needs the task, not its pet: the pet is looked up from
        task.pet_id and Pet.complete_task does the work. The next copy is due
        `on` + 1 day (daily) or + 7 days (weekly), with `on` defaulting to
        today. Returns that copy, or None if the task does not repeat or
        belongs to no pet of this owner.
        """
        pet = self.pet_for(task)
        if pet is None:
            return None
        return pet.complete_task(task.task_id, on)

    def get_conflicts(self) -> list[str]:
        """Return the warnings found while building the last plan."""
        return list(self.conflicts)

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
        self.conflicts = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                task.clear_schedule()
