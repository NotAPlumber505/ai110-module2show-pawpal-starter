from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

# Numeric rank for sorting: lower number = higher urgency
PRIORITY_RANK = {"high": 1, "medium": 2, "low": 3}


def _hhmm_to_minutes(time_str: str) -> int:
    """Convert a 'HH:MM' string to total minutes since midnight.

    'HH:MM' strings sort lexicographically the same as chronologically
    ('09:00' < '10:30') because Python compares character by character and
    the zero-padded format keeps digit width consistent. Converting to an
    integer enables arithmetic such as computing task end times for
    overlap detection.
    """
    h, m = time_str.split(":")
    return int(h) * 60 + int(m)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: str            # "high", "medium", or "low"
    category: str            # e.g. "walk", "feeding", "medication", "grooming"
    completed: bool = False
    recurring: bool = False  # Daily-pool flag: resets each day via reset()
    time_of_day: str = ""    # Optional scheduled start time in "HH:MM" (e.g. "08:30")
    frequency: str = ""      # "" = one-time | "daily" | "weekly"
    due_date: str = ""       # Next due date "YYYY-MM-DD"; set automatically by spawn_next()

    def mark_complete(self) -> None:
        """Mark this task as completed for this session."""
        self.completed = True

    def spawn_next(self) -> Optional[Task]:
        """Return a new Task for the next occurrence, or None if this is a one-time task.

        How timedelta works:
            from datetime import date, timedelta
            tomorrow  = date.today() + timedelta(days=1)  # one day forward
            next_week = date.today() + timedelta(days=7)  # seven days forward

        timedelta represents a fixed calendar duration. Adding it to a date
        object shifts that date forward by the given number of days.
        str(date) produces the 'YYYY-MM-DD' string stored in due_date.

        Only tasks with frequency='daily' or frequency='weekly' produce a
        next occurrence.  One-time tasks (frequency='') return None.
        """
        if not self.frequency:
            return None
        days_ahead = 1 if self.frequency == "daily" else 7
        next_due = date.today() + timedelta(days=days_ahead)
        return Task(
            name=self.name,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            recurring=self.recurring,
            time_of_day=self.time_of_day,
            frequency=self.frequency,
            due_date=str(next_due),
        )

    def reset(self) -> None:
        """Reset a recurring task so it re-enters the pool on the next plan."""
        self.completed = False

    def update(self, name: str, duration_minutes: int, priority: str) -> None:
        """Edit the task's name, duration, and priority.

        Validates priority against PRIORITY_RANK so bad values are rejected
        at the boundary rather than silently stored.
        """
        if priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        self.name = name
        self.duration_minutes = duration_minutes
        self.priority = priority

    def is_high_priority(self) -> bool:
        """Return True if this task has the highest priority level."""
        return self.priority == "high"


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
        self._tasks.append(task)

    def remove_task(self, task_name: str) -> bool:
        """Remove a task by name. Returns True if a task was removed, False if not found."""
        original_count = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.name != task_name]
        return len(self._tasks) < original_count

    def complete_task(self, task_name: str) -> Optional[Task]:
        """Mark a named incomplete task as done and auto-spawn the next occurrence.

        This is the correct entry point for completing a frequency-based task.
        It keeps all spawning logic in one place so callers never need to
        manage due-date arithmetic themselves:

          1. Finds the first incomplete task with the given name.
          2. Calls mark_complete() on it.
          3. Calls spawn_next() — if the task has a frequency, a new Task
             instance with an updated due_date is created and appended.
          4. Returns the new Task, or None for one-time tasks.

        Task stays a pure data object: it knows how to describe its next
        occurrence (spawn_next) but never modifies any list itself.
        """
        for task in self._tasks:
            if task.name == task_name and not task.completed:
                task.mark_complete()
                next_task = task.spawn_next()
                if next_task:
                    self._tasks.append(next_task)
                return next_task
        return None

    def get_tasks(self) -> List[Task]:
        """Return all tasks associated with this pet."""
        return list(self._tasks)

    def get_completed_tasks(self) -> List[Task]:
        """Return only tasks that have been marked complete."""
        return [t for t in self._tasks if t.completed]

    def get_incomplete_tasks(self) -> List[Task]:
        """Return only tasks that have not been completed (includes recurring tasks)."""
        return [t for t in self._tasks if not t.completed or t.recurring]

    def reset_recurring_tasks(self) -> None:
        """Reset all recurring tasks so they re-enter the next day's plan."""
        for task in self._tasks:
            if task.recurring:
                task.reset()

    def get_profile(self) -> str:
        """Return a formatted summary of the pet's information."""
        owner_name = self.owner.name if self.owner else "unassigned"
        return f"{self.name} ({self.species}, age {self.age}) — owner: {owner_name}"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str, daily_available_minutes: int, preferences: str = ""):
        if daily_available_minutes < 0:
            raise ValueError("daily_available_minutes cannot be negative")
        self.name = name
        self.daily_available_minutes = daily_available_minutes
        self.preferences = preferences
        self._pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Associate a pet with this owner and set the back-reference on the pet."""
        pet.owner = self
        self._pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return the list of pets owned by this owner."""
        return list(self._pets)

    def set_availability(self, minutes: int) -> None:
        """Update the owner's daily available time in minutes."""
        if minutes < 0:
            raise ValueError("Available minutes cannot be negative")
        self.daily_available_minutes = minutes


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves tasks from all of an owner's pets, sorts by priority then
    duration (shortest-first within a tier), and greedily fits them into
    the owner's available daily time."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.available_minutes = owner.daily_available_minutes
        self.plan: List[Task] = []

    # --- Internal helpers ---------------------------------------------------

    def _all_eligible_tasks(self) -> List[Task]:
        """Collect every schedulable task across all pets.

        Algorithm simplification: refactored from a for-loop with .extend()
        to a single nested list comprehension:

            [item  for outer in collection  for item in outer  if condition]

        Both forms produce identical output. The comprehension removes the
        intermediate variable and the .extend() call, expressing the
        two-level iteration and filter condition as one readable statement.

        Recurring tasks are always included regardless of completion status.
        Non-recurring completed tasks are excluded.
        """
        return [
            t
            for pet in self.owner.get_pets()
            for t in pet.get_tasks()
            if t.recurring or not t.completed
        ]

    # --- Core scheduling ----------------------------------------------------

    def generate_plan(self) -> List[Task]:
        """Sort eligible tasks by (priority, duration) and fill available time.

        Sorting strategy:
          - Primary: priority rank (high -> medium -> low)
          - Secondary: duration ascending (shortest task first within a tier)
            This maximises the number of tasks that fit in the time budget.

        Resets the plan on each call so re-runs are always fresh.
        """
        self.plan = []
        self.available_minutes = self.owner.daily_available_minutes

        sorted_tasks = sorted(
            self._all_eligible_tasks(),
            key=lambda t: (PRIORITY_RANK.get(t.priority, 99), t.duration_minutes)
        )

        time_remaining = self.available_minutes
        for task in sorted_tasks:
            if task.duration_minutes <= time_remaining:
                self.plan.append(task)
                time_remaining -= task.duration_minutes

        return self.plan

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks sorted chronologically by their 'HH:MM' time_of_day.

        How 'HH:MM' string sorting works:
            Python compares strings character by character from left to right.
            Because times are zero-padded ('09:00', not '9:00'), string order
            always matches chronological order:
                '07:30' < '08:00' < '09:00' < '17:30'

            The lambda  key=lambda t: t.time_of_day or '99:99'  pushes tasks
            with no scheduled time_of_day to the end of the sorted list.

        Args:
            tasks: list to sort; defaults to self.plan when not provided.
        Returns:
            A new sorted list -- the original list is not mutated.
        """
        source = tasks if tasks is not None else self.plan
        return sorted(source, key=lambda t: t.time_of_day or "99:99")

    # --- Filtering ----------------------------------------------------------

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return only scheduled tasks that belong to the named pet.

        Uses object identity (id()) to match tasks against the pet's own list,
        so two tasks with identical names on different pets are never confused.
        """
        target = next(
            (p for p in self.owner.get_pets() if p.name.lower() == pet_name.lower()),
            None,
        )
        if target is None:
            return []
        pet_task_ids = {id(t) for t in target.get_tasks()}
        return [t for t in self.plan if id(t) in pet_task_ids]

    def filter_by_status(self, completed: bool) -> List[Task]:
        """Return tasks from the plan that match the given completion status."""
        return [t for t in self.plan if t.completed == completed]

    # --- Conflict detection -------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """Scan all pets for scheduling conflicts and return human-readable warnings.

        Lightweight strategy: returns warning strings rather than raising
        exceptions, so the app stays usable even when issues are present.

        Three checks are performed:
          1. Duplicate task names on the same pet.
          2. A pet's total task time exceeding the owner's daily budget.
          3. Time-slot overlaps between any two scheduled tasks that have a
             time_of_day set (an owner cannot do two things simultaneously).

        Overlap logic (standard interval intersection test):
            Two intervals [start_a, end_a) and [start_b, end_b) overlap when:
                start_a < end_b  AND  start_b < end_a
            Times are converted from 'HH:MM' to integer minutes via
            _hhmm_to_minutes() so arithmetic is straightforward.
        """
        warnings: List[str] = []

        for pet in self.owner.get_pets():
            tasks = pet.get_tasks()

            # Check 1 -- Duplicate task names on the same pet
            seen_names: set = set()
            for task in tasks:
                if task.name in seen_names:
                    warnings.append(
                        f"Duplicate task '{task.name}' found for {pet.name}."
                    )
                seen_names.add(task.name)

            # Check 2 -- Total time overload for this pet
            total = sum(t.duration_minutes for t in tasks if not t.completed or t.recurring)
            if total > self.owner.daily_available_minutes:
                over = total - self.owner.daily_available_minutes
                warnings.append(
                    f"{pet.name}'s tasks total {total} min, which is "
                    f"{over} min over today's {self.owner.daily_available_minutes}-min budget."
                )

        # Check 3 -- Time-slot overlaps across all scheduled timed tasks
        timed = [t for t in self.plan if t.time_of_day]
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                start_a = _hhmm_to_minutes(a.time_of_day)
                end_a   = start_a + a.duration_minutes
                start_b = _hhmm_to_minutes(b.time_of_day)
                end_b   = start_b + b.duration_minutes
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"Time conflict: '{a.name}' ({a.time_of_day}, {a.duration_minutes} min) "
                        f"overlaps with '{b.name}' ({b.time_of_day}, {b.duration_minutes} min)."
                    )

        return warnings

    # --- Explanation & unscheduled ------------------------------------------

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the scheduled plan."""
        if not self.plan:
            return "No tasks scheduled. Add tasks and run generate_plan() first."

        time_used = sum(t.duration_minutes for t in self.plan)
        lines = [
            f"Daily plan for {self.owner.name} "
            f"({self.available_minutes} min available):\n"
        ]
        for task in self.plan:
            recurring_label = " ↻" if task.recurring else ""
            time_label = f" @ {task.time_of_day}" if task.time_of_day else ""
            lines.append(
                f"  • [{task.priority.upper()}] {task.name}{recurring_label}{time_label}"
                f" — {task.duration_minutes} min ({task.category})"
            )
        lines.append(f"\nTime used: {time_used} / {self.available_minutes} min")

        skipped = self.get_unscheduled_tasks()
        if skipped:
            lines.append(f"\nSkipped -- {len(skipped)} task(s) didn't fit:")
            for task in skipped:
                lines.append(f"  x {task.name} ({task.duration_minutes} min)")

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("\nWarnings:")
            for warning in conflicts:
                lines.append(f"  ! {warning}")

        return "\n".join(lines)

    def get_unscheduled_tasks(self) -> List[Task]:
        """Return eligible tasks that did not make it into the plan."""
        scheduled = {id(t) for t in self.plan}
        return [t for t in self._all_eligible_tasks() if id(t) not in scheduled]
