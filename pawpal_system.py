from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: str          # "high", "medium", or "low"
    category: str          # e.g. "walk", "feeding", "medication", "grooming"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass

    def update(self, name: str, duration_minutes: int, priority: str) -> None:
        """Edit the task's name, duration, and priority."""
        pass

    def is_high_priority(self) -> bool:
        """Return True if this task has the highest priority level."""
        pass


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    owner: Owner = field(default=None, repr=False)
    _tasks: List[Task] = field(default_factory=list, init=False, repr=False)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        pass

    def get_tasks(self) -> List[Task]:
        """Return all tasks associated with this pet."""
        pass

    def get_profile(self) -> str:
        """Return a formatted summary of the pet's information."""
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, daily_available_minutes: int, preferences: str = ""):
        self.name = name
        self.daily_available_minutes = daily_available_minutes
        self.preferences = preferences
        self._pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Associate a pet with this owner."""
        pass

    def get_pets(self) -> List[Pet]:
        """Return the list of pets owned by this owner."""
        pass

    def set_availability(self, minutes: int) -> None:
        """Update the owner's daily available time in minutes."""
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, pet: Pet, available_minutes: int):
        self.pet = pet
        self.available_minutes = available_minutes
        self.plan: List[Task] = []

    def generate_plan(self) -> List[Task]:
        """Sort tasks by priority and fit them into available time.
        
        Returns the ordered list of tasks that fit within available_minutes.
        """
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the scheduled plan."""
        pass

    def get_unscheduled_tasks(self) -> List[Task]:
        """Return tasks that did not fit into today's schedule."""
        pass
