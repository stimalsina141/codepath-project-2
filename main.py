"""Terminal testing ground for PawPal+.

Builds a small owner/pet/task setup and prints today's schedule, so the
scheduling logic can be checked without running Streamlit.

Run it with:  python main.py
"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

# A fixed Tuesday, so the demo prints the same thing whatever day it is run.
DEMO_DATE = date(2026, 10, 13)


def build_demo_owner() -> Owner:
    """Create one owner with two pets and a handful of care tasks."""
    owner = Owner(
        owner_id="o1",
        name="Jordan",
        email="jordan@example.com",
        available_minutes=75,
    )

    mochi = Pet(pet_id="p1", name="Mochi", species="dog", breed="Shiba Inu", age=3)
    pichu = Pet(pet_id="p2", name="Pichu", species="cat", breed="Tabby", age=6)
    owner.add_pet(mochi)
    owner.add_pet(pichu)

    # Tasks are added out of time order on purpose (hike, 08:45, then 08:00),
    # so the sorting demo below has something to fix.
    mochi.add_task(
        Task(
            task_id="t3",
            title="Long hike",
            duration_minutes=90,
            priority="low",
            category="exercise",
        )
    )
    mochi.add_task(
        Task(
            task_id="t2",
            title="Breakfast",
            duration_minutes=10,
            priority="high",
            category="feeding",
            preferred_time="08:45",
        )
    )
    mochi.add_task(
        Task(
            task_id="t1",
            title="Morning walk",
            duration_minutes=30,
            priority="high",
            category="exercise",
            preferred_time="08:00",
        )
    )

    pichu.add_task(
        Task(
            task_id="t4",
            title="Medication",
            duration_minutes=5,
            priority="high",
            category="health",
            preferred_time="9:00",  # typed without the leading zero,
        )
    )
    pichu.add_task(
        Task(
            task_id="t6",
            title="Nail trim",
            duration_minutes=20,
            priority="low",
            category="grooming",
            recurrence="weekly",
            days=["monday"],
        )
    )
    pichu.add_task(
        Task(
            task_id="t5",
            title="Brushing",
            duration_minutes=15,
            priority="medium",
            category="grooming",
        )
    )

    return owner


RULE = "-" * 72


def pet_name(scheduler: Scheduler, task: Task) -> str:
    """Return the name of the pet a task belongs to, for display."""
    pet = scheduler.pet_for(task)
    return pet.name if pet else "unknown"


def print_schedule(scheduler: Scheduler, owner: Owner, on: date = DEMO_DATE) -> None:
    """Print the day's plan, any conflicts, then anything that did not fit.

    Each row carries its own reason, so the plan explains itself without a
    second pass over the same tasks.
    """
    plan = scheduler.generate_plan(on=on)

    print(f"\nToday's Schedule for {owner.name} ({on:%A %b %d})")
    print(f"Time budget: {scheduler.available_minutes} min | starting at {scheduler.start_time}")
    print(RULE)
    print(f"  {'TIME':<6} {'TASK':<15} {'PET':<7} {'LENGTH':>7}  {'PRIORITY':<9} WHY")
    print(RULE)

    if not plan:
        print("  Nothing fit in today's budget.")
    for task in plan:
        print(
            f"  {task.scheduled_time():<6} {task.title:<15} {pet_name(scheduler, task):<7} "
            f"{task.duration_minutes:>3} min  {task.priority:<9} {task.reason}"
        )

    used = sum(task.duration_minutes for task in plan)
    print(RULE)
    print(f"  {len(plan)} task(s) planned, {used} of {scheduler.available_minutes} min used")

    for warning in scheduler.get_conflicts():
        print(f"  ! {warning}")

    skipped = scheduler.get_skipped_tasks()
    if skipped:
        print("\nDidn't fit today:")
        for task in skipped:
            print(
                f"  {task.title:<15} {pet_name(scheduler, task):<7} {task.duration_minutes:>3} min  "
                f"{task.priority:<9} {task.reason}"
            )


def print_task_list(scheduler: Scheduler, heading: str, tasks: list[Task]) -> None:
    """Print a plain list of tasks under a heading, for the sort/filter demos."""
    print(f"\n{heading}")
    if not tasks:
        print("  (none)")
    for task in tasks:
        when = task.time_string() or "--:--"
        status = "done" if task.completed else "pending"
        due = f", due {task.due_date:%b %d}" if task.due_date else ""
        print(f"  {when}  {task.title:<13} {pet_name(scheduler, task):<6} {status}{due}")


def main() -> None:
    """Walk through each scheduling feature in turn, printing the results."""
    owner = build_demo_owner()
    print(f"{owner.name} has {len(owner.pets)} pets and {owner.total_task_count()} tasks total.")
    for pet in owner.pets:
        print(f"  - {pet.name} the {pet.species}: {len(pet.tasks)} task(s), "
              f"{pet.total_duration()} min of care")

    # Sorting: filter_tasks() with no arguments returns tasks in the order
    # they were added; sort_by_time() puts them in clock order, untimed last.
    scheduler = Scheduler(owner)
    print("\n" + "=" * 60)
    print("Sorting and filtering")
    every_task = scheduler.filter_tasks()
    print_task_list(scheduler, "In the order they were added:", every_task)
    print_task_list(scheduler, "Sorted by time:", scheduler.sort_by_time(every_task))

    # Filtering by pet name (any case) and by completion status.
    print_task_list(
        scheduler, "Just Mochi, by time:", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="mochi"))
    )
    mochi = owner.get_pet("p1")
    mochi.get_tasks()[1].mark_complete()  # Breakfast, done for the moment
    print("\n(Breakfast marked done)")
    print_task_list(scheduler, "Still pending:", scheduler.sort_by_time(scheduler.filter_tasks(completed=False)))
    print_task_list(scheduler, "Done:", scheduler.filter_tasks(completed=True))
    print_task_list(
        scheduler,
        "Pichu's pending tasks:",
        scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Pichu", completed=False)),
    )
    mochi.get_tasks()[1].reopen()

    # A normal weekday: the weekly nail trim is not due. Tasks are laid out
    # in clock order, and the flexible brushing fills the gap before 08:45.
    print("\n" + "=" * 60)
    print_schedule(scheduler, owner)

    # Same tasks, but a much tighter budget shows the budget filter at work.
    print("\n" + "=" * 60)
    print("What if Jordan only had 25 minutes today?")
    print_schedule(Scheduler(owner, available_minutes=25), owner)

    # Completing a recurring task queues the next one instead of losing it:
    # daily tasks come back tomorrow, weekly ones in seven days.
    print("\n" + "=" * 60)
    print(f"Recurring tasks, completed on {DEMO_DATE:%A %b %d}:")
    for task_id in ("t2", "t6"):  # Breakfast (daily), Nail trim (weekly)
        done = next(t for t in scheduler.filter_tasks() if t.task_id == task_id)
        follow_up = scheduler.mark_task_complete(done, on=DEMO_DATE)
        print(f"  {done.title} ({done.recurrence}) done -> next one due {follow_up.due_date:%A %b %d}")
    print_task_list(scheduler, "All tasks now:", scheduler.sort_by_time(scheduler.filter_tasks()))

    # Two tasks asking for overlapping times produce a conflict warning.
    print("\n" + "=" * 60)
    print("Pichu's vet call is booked at 08:15, in the middle of Mochi's walk:")
    owner.get_pet("p2").add_task(
        Task(
            task_id="t7",
            title="Vet call",
            duration_minutes=15,
            priority="high",
            category="health",
            preferred_time="08:15",
            recurrence="once",
        )
    )
    print_schedule(Scheduler(owner), owner)


if __name__ == "__main__":
    main()
