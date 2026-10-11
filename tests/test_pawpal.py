"""Tests for the PawPal+ logic layer.

Run with:  pytest
"""

from pawpal_system import Pet, Task


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
