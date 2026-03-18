import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Task


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
