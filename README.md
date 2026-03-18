# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smarter Scheduling

PawPal+ includes several scheduling enhancements beyond basic priority sorting:

- **Time-of-day sorting** — Each `Task` accepts an optional `time_of_day` field in `"HH:MM"` format. `Scheduler.sort_by_time()` returns a chronologically ordered copy of any task list. Zero-padded time strings sort lexicographically in the correct order (`"07:30" < "08:00" < "17:30"`), so a simple lambda is all that's needed — no datetime parsing required.

- **Filtering** — `filter_by_pet(name)` returns only the plan's tasks for a specific pet, using object identity so tasks with identical names on different pets are never confused. `filter_by_status(completed)` returns tasks that match a given completion state.

- **Recurring tasks with auto-spawn** — Tasks with `frequency="daily"` or `frequency="weekly"` automatically generate the next occurrence when completed via `pet.complete_task(name)`. The new task's `due_date` is calculated with Python's `timedelta` (`date.today() + timedelta(days=1)` for daily). The original task is marked complete; the new instance is appended and re-enters the next plan fresh.

- **Conflict detection** — `Scheduler.detect_conflicts()` runs three checks: duplicate task names on the same pet, per-pet time budget overruns, and time-slot overlaps between any two timed tasks. Overlaps are detected with the standard interval intersection test (`start_a < end_b AND start_b < end_a`). Warnings are returned as strings rather than exceptions, keeping the app usable even when issues exist.

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest
```

Current tests cover core scheduler reliability: task completion status updates, adding tasks to pets, chronological sorting by `HH:MM`, daily recurrence auto-spawning with tomorrow's due date, and conflict detection for duplicate/overlapping times.
