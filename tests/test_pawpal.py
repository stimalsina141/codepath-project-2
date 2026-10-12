"""Tests for the PawPal+ logic layer.

Run with:  pytest
"""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

TUESDAY = date(2026, 10, 13)


def make_owner(*tasks_by_pet: list[Task], minutes: int = 120) -> Owner:
    """Build an owner with one pet per task list."""
    owner = Owner(owner_id="o1", name="Jordan", available_minutes=minutes)
    for index, tasks in enumerate(tasks_by_pet, start=1):
        pet = Pet(pet_id=f"p{index}", name=f"Pet{index}", species="dog")
        for task in tasks:
            pet.add_task(task)
        owner.add_pet(pet)
    return owner


def task(task_id: str, minutes: int, priority: str = "high", at: str | None = None, **extra) -> Task:
    """Shorthand for building a Task in tests."""
    return Task(
        task_id=task_id,
        title=task_id,
        duration_minutes=minutes,
        priority=priority,
        preferred_time=at,
        **extra,
    )


def test_mark_complete_changes_task_status():
    """A task starts out pending, and mark_complete() flips it to done."""
    task = Task(
        task_id="t1",
        title="Morning walk",
        duration_minutes=30,
        priority="high",
    )

    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_a_task_increases_the_pets_task_count():
    """A pet starts with no tasks, and add_task() grows the list."""
    pet = Pet(pet_id="p1", name="Mochi", species="dog")

    assert len(pet.get_tasks()) == 0

    pet.add_task(
        Task(task_id="t1", title="Morning walk", duration_minutes=30, priority="high")
    )

    assert len(pet.get_tasks()) == 1

    pet.add_task(
        Task(task_id="t2", title="Breakfast", duration_minutes=10, priority="high")
    )

    assert len(pet.get_tasks()) == 2


# --- Sorting by time --------------------------------------------------------


def test_plan_is_in_clock_order_not_priority_order():
    """A short high-priority 09:00 task must not push an 08:00 task later."""
    owner = make_owner([task("walk", 30, at="08:00"), task("meds", 5, at="09:00")])
    plan = Scheduler(owner).generate_plan(on=TUESDAY)

    assert [t.title for t in plan] == ["walk", "meds"]
    assert [t.scheduled_time() for t in plan] == ["08:00", "09:00"]


def test_flexible_task_fills_gap_before_a_timed_task():
    owner = make_owner([task("walk", 30, at="08:00"), task("feed", 10, at="09:00"), task("brush", 15, "low")])
    plan = Scheduler(owner).generate_plan(on=TUESDAY)

    assert [(t.title, t.scheduled_time()) for t in plan] == [
        ("walk", "08:00"),
        ("brush", "08:30"),
        ("feed", "09:00"),
    ]


def test_flexible_task_too_long_for_gap_goes_after():
    owner = make_owner([task("feed", 10, at="08:10"), task("hike", 60)])
    plan = Scheduler(owner).generate_plan(on=TUESDAY)

    assert [(t.title, t.scheduled_time()) for t in plan] == [("feed", "08:10"), ("hike", "08:20")]


def test_sort_by_time_puts_untimed_tasks_last():
    tasks = [task("later", 5, at="10:00"), task("anytime", 5), task("early", 5, at="07:30")]
    ordered = Scheduler(make_owner([])).sort_by_time(tasks)

    assert [t.title for t in ordered] == ["early", "later", "anytime"]


def test_sort_by_time_handles_unpadded_times():
    """A hand-typed "8:00" must still sort before "10:00", not after it."""
    tasks = [task("ten", 5, at="10:00"), task("eight", 5, at="8:00")]
    ordered = Scheduler(make_owner([])).sort_by_time(tasks)

    assert [t.title for t in ordered] == ["eight", "ten"]


# --- Filtering --------------------------------------------------------------


def test_filter_tasks_by_pet_and_status():
    done = task("done", 5)
    done.mark_complete()
    owner = make_owner([task("a", 5), done], [task("b", 5)])
    scheduler = Scheduler(owner)

    assert [t.title for t in scheduler.filter_tasks(pet_id="p1")] == ["a", "done"]
    assert [t.title for t in scheduler.filter_tasks(completed=False)] == ["a", "b"]
    assert [t.title for t in scheduler.filter_tasks(pet_id="p1", completed=True)] == ["done"]
    assert len(scheduler.filter_tasks()) == 3


def test_filter_tasks_by_pet_name_ignores_case():
    done = task("done", 5)
    done.mark_complete()
    owner = make_owner([task("a", 5), done], [task("b", 5)])
    scheduler = Scheduler(owner)

    assert [t.title for t in scheduler.filter_tasks(pet_name="pet1")] == ["a", "done"]
    assert [t.title for t in scheduler.filter_tasks(pet_name="Pet1", completed=False)] == ["a"]
    assert scheduler.filter_tasks(pet_name="nobody") == []


# --- Recurring tasks --------------------------------------------------------


def test_completing_daily_task_queues_tomorrows_copy():
    owner = make_owner([task("feed", 10)])
    pet = owner.get_pet("p1")

    follow_up = pet.complete_task("feed", on=TUESDAY)

    assert pet.tasks[0].completed is True
    assert follow_up is not None and follow_up.completed is False
    assert follow_up.due_date == date(2026, 10, 14)
    assert follow_up.task_id != "feed"
    assert len(pet.tasks) == 2


def test_completing_weekly_task_queues_next_week():
    owner = make_owner([task("trim", 20, recurrence="weekly")])
    follow_up = owner.get_pet("p1").complete_task("trim", on=TUESDAY)

    assert follow_up.due_date == date(2026, 10, 20)


def test_scheduler_mark_task_complete_queues_next_daily_copy():
    owner = make_owner([task("feed", 10, at="08:45")])
    scheduler = Scheduler(owner)
    feed = owner.get_pet("p1").tasks[0]

    follow_up = scheduler.mark_task_complete(feed, on=TUESDAY)

    assert feed.completed is True
    assert follow_up.due_date == TUESDAY + timedelta(days=1)
    assert follow_up.pet_id == "p1" and follow_up.preferred_time == "08:45"
    assert follow_up in owner.get_pet("p1").tasks


def test_scheduler_mark_task_complete_defaults_to_today():
    owner = make_owner([task("trim", 20, recurrence="weekly")])
    scheduler = Scheduler(owner)

    follow_up = scheduler.mark_task_complete(owner.get_pet("p1").tasks[0])

    assert follow_up.due_date == date.today() + timedelta(days=7)


def test_scheduler_mark_task_complete_ignores_unknown_task():
    scheduler = Scheduler(make_owner([task("feed", 10)]))
    stray = task("stray", 5)

    assert scheduler.mark_task_complete(stray, on=TUESDAY) is None
    assert stray.completed is False


def test_reopening_a_task_removes_its_queued_copy():
    owner = make_owner([task("feed", 10)])
    pet = owner.get_pet("p1")
    pet.complete_task("feed", on=TUESDAY)

    pet.reopen_task("feed")

    assert [(t.task_id, t.completed) for t in pet.tasks] == [("feed", False)]


def test_one_off_task_does_not_repeat():
    owner = make_owner([task("vet", 30, recurrence="once")])
    pet = owner.get_pet("p1")

    assert pet.complete_task("vet", on=TUESDAY) is None
    assert len(pet.tasks) == 1


def test_next_occurrence_is_not_planned_before_its_due_date():
    owner = make_owner([task("feed", 10)])
    owner.get_pet("p1").complete_task("feed", on=TUESDAY)

    assert Scheduler(owner).generate_plan(on=TUESDAY) == []
    tomorrow = Scheduler(owner).generate_plan(on=date(2026, 10, 14))
    assert [t.title for t in tomorrow] == ["feed"]


def test_weekly_task_only_due_on_its_days():
    owner = make_owner([task("trim", 20, recurrence="weekly", days=["monday"])])

    assert Scheduler(owner).generate_plan(on=TUESDAY) == []
    assert len(Scheduler(owner).generate_plan(on=date(2026, 10, 12))) == 1


# --- Conflict detection -----------------------------------------------------


def test_overlapping_preferred_times_are_reported():
    owner = make_owner([task("walk", 30, at="08:00")], [task("vet", 15, at="08:15")])
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(on=TUESDAY)

    conflicts = scheduler.get_conflicts()
    assert len(conflicts) == 1
    assert "vet" in conflicts[0] and "walk" in conflicts[0]
    # The plan itself never double-books: vet waits for the walk to end.
    assert [t.scheduled_time() for t in plan] == ["08:00", "08:30"]


def test_same_time_for_same_pet_is_reported():
    owner = make_owner([task("walk", 30, at="08:00"), task("feed", 10, at="08:00")])
    scheduler = Scheduler(owner)
    scheduler.generate_plan(on=TUESDAY)

    assert scheduler.get_conflicts()[0] == (
        "Same time: Pet1's 'feed' and Pet1's 'walk' both want 08:00 (same pet)"
    )


def test_same_time_across_pets_is_reported():
    owner = make_owner([task("walk", 30, at="08:00")], [task("meds", 5, at="08:00")])
    scheduler = Scheduler(owner)
    scheduler.generate_plan(on=TUESDAY)

    same_time = [c for c in scheduler.get_conflicts() if c.startswith("Same time")]
    assert len(same_time) == 1
    assert "Pet1's 'walk'" in same_time[0] and "Pet2's 'meds'" in same_time[0]
    assert same_time[0].endswith("(different pets)")


def test_three_tasks_at_same_time_report_every_pair():
    """Each of the three pairs clashes, so all three are reported."""
    owner = make_owner([task("walk", 30, at="08:00"), task("feed", 10, at="08:00")], [task("meds", 5, at="08:00")])
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(on=TUESDAY)

    assert len([c for c in scheduler.get_conflicts() if c.startswith("Same time")]) == 3
    # Warnings only: every task is still planned, one after another.
    assert len(plan) == 3


def test_long_task_overlapping_several_later_ones_reports_each():
    owner = make_owner([task("hike", 90, at="08:00"), task("feed", 10, at="08:30"), task("meds", 5, at="09:00")])
    scheduler = Scheduler(owner)
    scheduler.generate_plan(on=TUESDAY)

    overlaps = [c for c in scheduler.get_conflicts() if c.startswith("Overlap")]
    assert len(overlaps) == 2


def test_back_to_back_tasks_are_not_a_conflict():
    owner = make_owner([task("walk", 30, at="08:00"), task("feed", 10, at="08:30")])
    scheduler = Scheduler(owner)
    scheduler.generate_plan(on=TUESDAY)

    assert scheduler.get_conflicts() == []


def test_task_pushed_well_past_its_time_is_reported_late():
    owner = make_owner([task("hike", 60, at="08:00"), task("feed", 10, at="08:10")])
    scheduler = Scheduler(owner)
    scheduler.generate_plan(on=TUESDAY)

    assert any(c.startswith("Late: Pet1's 'feed'") for c in scheduler.get_conflicts())
