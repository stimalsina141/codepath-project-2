"""Terminal testing ground for PawPal+.

Builds a small owner/pet/task setup and prints today's schedule, so the
scheduling logic can be checked without running Streamlit.

Run it with:  python main.py
"""

from pawpal_system import Owner, Pet, Scheduler, Task


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
            task_id="t3",
            title="Long hike",
            duration_minutes=90,
            priority="low",
            category="exercise",
        )
    )

    pichu.add_task(
        Task(
            task_id="t4",
            title="Medication",
            duration_minutes=5,
            priority="high",
            category="health",
            preferred_time="09:00",
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

    return owner


RULE = "-" * 72


def print_schedule(scheduler: Scheduler, owner: Owner, day: str) -> None:
    """Print today's plan, then anything that did not fit.

    Each row carries its own reason, so the plan explains itself without a
    second pass over the same tasks.
    """
    plan = scheduler.generate_plan(day=day)

    print(f"\nToday's Schedule for {owner.name} ({day.title()})")
    print(f"Time budget: {scheduler.available_minutes} min | starting at {scheduler.start_time}")
    print(RULE)
    print(f"  {'TIME':<6} {'TASK':<15} {'PET':<7} {'LENGTH':>7}  {'PRIORITY':<9} WHY")
    print(RULE)

    if not plan:
        print("  Nothing fit in today's budget.")
    for task in plan:
        pet = scheduler.pet_for(task)
        pet_name = pet.name if pet else "unknown"
        print(
            f"  {task.scheduled_time():<6} {task.title:<15} {pet_name:<7} "
            f"{task.duration_minutes:>3} min  {task.priority:<9} {task.reason}"
        )

    used = sum(task.duration_minutes for task in plan)
    print(RULE)
    print(f"  {len(plan)} task(s) planned, {used} of {scheduler.available_minutes} min used")

    skipped = scheduler.get_skipped_tasks()
    if skipped:
        print("\nDidn't fit today:")
        for task in skipped:
            pet = scheduler.pet_for(task)
            pet_name = pet.name if pet else "unknown"
            print(
                f"  {task.title:<15} {pet_name:<7} {task.duration_minutes:>3} min  "
                f"{task.priority:<9} {task.reason}"
            )


def main() -> None:
    owner = build_demo_owner()
    print(f"{owner.name} has {len(owner.pets)} pets and {owner.total_task_count()} tasks total.")
    for pet in owner.pets:
        print(f"  - {pet.name} the {pet.species}: {len(pet.tasks)} task(s), "
              f"{pet.total_duration()} min of care")

    # A normal weekday: the weekly nail trim is not due.
    print_schedule(Scheduler(owner), owner, day="tuesday")

    # Same tasks, but a much tighter budget shows the filtering work.
    print("\n" + "=" * 60)
    print("What if Jordan only had 25 minutes today?")
    print_schedule(Scheduler(owner, available_minutes=25), owner, day="tuesday")


if __name__ == "__main__":
    main()
