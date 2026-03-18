import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() should set completed to True."""
    task = Task(name="Morning walk", duration_minutes=30, priority="high", category="walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Biscuit", species="Dog", age=3)
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(name="Feeding", duration_minutes=10, priority="high", category="feeding"))
    assert len(pet.get_tasks()) == 1


def test_sort_by_time_returns_chronological_order():
    """Tasks should be sorted from earliest to latest HH:MM time."""
    owner = Owner(name="Jordan", daily_available_minutes=120)
    pet = Pet(name="Biscuit", species="Dog", age=3)
    owner.add_pet(pet)

    pet.add_task(Task(name="Evening walk", duration_minutes=20, priority="medium", category="walk", time_of_day="17:30"))
    pet.add_task(Task(name="Breakfast", duration_minutes=10, priority="high", category="feeding", time_of_day="08:00"))
    pet.add_task(Task(name="Morning walk", duration_minutes=30, priority="high", category="walk", time_of_day="07:30"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    sorted_names = [t.name for t in scheduler.sort_by_time()]

    assert sorted_names == ["Morning walk", "Breakfast", "Evening walk"]


def test_complete_daily_task_spawns_next_day_task():
    """Completing a daily task should append a new task due tomorrow."""
    pet = Pet(name="Luna", species="Cat", age=5)
    pet.add_task(
        Task(
            name="Feeding",
            duration_minutes=10,
            priority="high",
            category="feeding",
            frequency="daily",
            time_of_day="08:30",
        )
    )

    next_task = pet.complete_task("Feeding")
    tasks = pet.get_tasks()

    assert next_task is not None
    assert len(tasks) == 2
    assert tasks[0].completed is True
    assert next_task.name == "Feeding"
    assert next_task.completed is False
    assert next_task.due_date == str(date.today() + timedelta(days=1))


def test_detect_conflicts_flags_duplicate_times():
    """Two tasks with overlapping time slots should be flagged as a time conflict."""
    owner = Owner(name="Jordan", daily_available_minutes=180)
    pet = Pet(name="Biscuit", species="Dog", age=3)
    owner.add_pet(pet)

    pet.add_task(Task(name="Task A", duration_minutes=30, priority="high", category="walk", time_of_day="08:00"))
    pet.add_task(Task(name="Task B", duration_minutes=15, priority="high", category="medication", time_of_day="08:00"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    warnings = scheduler.detect_conflicts()

    assert any("Time conflict" in warning for warning in warnings)
