# PawPal+ Project Reflection

## 1. System Design

**Core User Actions**

The three core actions a user must be able to perform are:

1. **Add a pet** — The owner enters basic information about themselves and their pet (name, species, age) to create a profile. This profile becomes the context for all scheduling decisions, ensuring that tasks are tailored to a specific animal and owner.

2. **Schedule a task** — The owner creates a care task (such as a walk, feeding, medication, grooming, or enrichment activity) by providing a task name, an estimated duration in minutes, and a priority level. Tasks can also be edited or removed as the pet's needs change.

3. **See today's tasks** — The owner requests a generated daily plan. The app evaluates all pending tasks against the owner's available time and task priorities, then displays an ordered schedule for the day along with an explanation of why each task was included or excluded.

---

**Four Core Classes**

**1. Owner**
Represents the person using the app.
- *Attributes:* `name`, `daily_available_minutes` (total time they can dedicate to pet care each day), `preferences` (optional notes like preferred walk times)
- *Methods:* `add_pet(pet)` — associates a pet with this owner; `get_pets()` — returns the list of owned pets; `set_availability(minutes)` — updates available time

**2. Pet**
Represents the animal being cared for.
- *Attributes:* `name`, `species`, `age`, `owner` (reference to the Owner)
- *Methods:* `add_task(task)` — appends a task to the pet's task list; `get_tasks()` — returns all tasks for this pet; `get_profile()` — returns a formatted summary of the pet's info

**3. Task**
Represents a single care activity to be scheduled.
- *Attributes:* `name`, `duration_minutes`, `priority` (e.g., 1–3 or "high/medium/low"), `category` (e.g., "walk", "feeding", "medication"), `completed` (boolean)
- *Methods:* `mark_complete()` — sets completed to True; `update(name, duration, priority)` — edits task details; `is_high_priority()` — returns True if priority is at the top level

**4. Scheduler**
Contains the logic for generating the daily plan.
- *Attributes:* `pet` (the Pet being scheduled for), `available_minutes` (copied from Owner), `plan` (the ordered list of scheduled Tasks)
- *Methods:* `generate_plan()` — sorts tasks by priority, then fits them into available time until time runs out; `explain_plan()` — returns a human-readable explanation of which tasks were included and why; `get_unscheduled_tasks()` — returns tasks that did not fit into the day

---

**a. Initial design**

The initial design centered on four classes with clearly separated responsibilities:

- **Owner** — holds the person's name, their total daily available time in minutes, and optional preferences (such as preferred walk times). It manages a list of associated pets and is the source of the time budget passed to the Scheduler.
- **Pet** — holds the animal's name, species, and age, along with a back-reference to its Owner. It owns and manages the list of Tasks assigned to it, acting as the bridge between the person and their care responsibilities.
- **Task** — represents a single atomic care activity. It stores what the task is (`name`, `category`), how long it takes (`duration_minutes`), how important it is (`priority`), and whether it has been done (`completed`). It carries no scheduling logic itself — it is pure data with a few convenience methods.
- **Scheduler** — is the only class that contains scheduling logic. It takes a Pet and an available time budget, queries the Pet's task list, sorts tasks by priority, and greedily fills the day until time runs out. It also produces a human-readable explanation of the resulting plan.

**b. Design changes**

Reviewing the skeleton against the UML revealed three issues that need to be addressed before implementing logic:

1. **Priority ordering requires an explicit rank map.** The `priority` attribute is stored as a plain string (`"high"`, `"medium"`, `"low"`), but Python would sort these alphabetically (h < l < m), placing "low" before "medium" — the opposite of the intended order. A constant mapping such as `{"high": 1, "medium": 2, "low": 3}` must be introduced so `generate_plan()` can sort correctly by numeric rank.

2. **`generate_plan()` must reset `self.plan` before each run.** As designed, calling `generate_plan()` a second time (for example, after a task is added or edited) would append a second copy of every task to the existing list. The method needs to clear `self.plan = []` at its start so re-runs always produce a fresh, accurate schedule.

3. **The Owner↔Pet back-reference must be managed in `add_pet()`.** `Pet` holds an `owner` field, but nothing in the skeleton ensures it is ever set. `Owner.add_pet()` must also assign `pet.owner = self` when it appends the pet, keeping both sides of the relationship consistent. Without this, `pet.owner` silently remains `None` even after the pet is registered.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The Scheduler evaluates three constraints in order of importance:

1. **Time budget** (`daily_available_minutes`): the hard outer limit. If a task does not fit in the remaining time it is skipped — no task is ever split.
2. **Priority** (`high`, `medium`, `low`): determines which tasks claim the budget first. `PRIORITY_RANK` maps each string to a number so tasks sort correctly before the fill loop runs.
3. **Duration as tie-breaker**: within the same priority tier, shorter tasks go first (shortest-job-first), maximising how many tasks complete in the window.

Time budget is the hardest constraint because over-committing leads to missed tasks. Priority is the primary sort key so health tasks (medication, feeding) are never crowded out by optional enrichment.

**b. Tradeoffs**

The scheduler uses a **greedy shortest-job-first** strategy rather than finding the mathematically optimal task combination. It may skip a single high-value 45-minute task in favour of fitting three shorter medium-priority tasks, even if the longer task represented more total care value. This is reasonable for pet care because completing more habitual tasks (walks, feeding, brushing) maintains an animal's routine better than fewer but longer sessions. The greedy approach also runs in O(n log n) versus exponential time for a full knapsack solution.

**Algorithm simplification — `_all_eligible_tasks()`**

Reviewing this helper showed a clear readability win. The original built a flat list with a `for`-loop and `.extend()`:

	tasks = []
	for pet in self.owner.get_pets():
		tasks.extend(t for t in pet.get_tasks() if t.recurring or not t.completed)
	return tasks

It was replaced with a nested list comprehension:

	return [
		t
		for pet in self.owner.get_pets()
		for t in pet.get_tasks()
		if t.recurring or not t.completed
	]

Both produce identical output. The comprehension removes the intermediate variable and the `.extend()` call, expressing the two-level iteration and filter as one statement. When a loop exists only to build and return a list, a comprehension is usually cleaner.

---

## 3. AI Collaboration

**a. How you used AI**

I used VS Code Copilot as a pair programmer across distinct phases: architecture drafting, implementation, debugging, and test expansion.

Most effective Copilot features for this scheduler were:

1. **Inline completions during class construction** - fast scaffolding for repetitive patterns (dataclass fields, getters, and method signatures).
2. **Chat-based refactoring support** - useful when converting plain loops to cleaner comprehensions and when reorganizing UI flow around `st.session_state`.
3. **Targeted test drafting** - high-value initial pytest skeletons for sorting, recurrence, and conflict checks that I then tightened with project-specific assertions.
4. **Context-aware code navigation** - quickly tracing where methods were consumed (`Scheduler` methods in `app.py`) before wiring UI features.

The most helpful prompts were specific and constraint-based, for example: "Sort by HH:MM chronologically, keep one-time tasks intact, and show conflicts as non-fatal warnings." Prompts that included acceptance criteria (input, expected output, edge case) produced the best results.

**b. Judgment and verification**

One AI suggestion initially proposed replacing large sections of files with broad patches that introduced formatting artifacts and duplicate lines. I rejected that approach and switched to smaller, targeted edits so I could verify each change in isolation.

I evaluated suggestions by applying three checks:

1. **Behavioral check** - does the change satisfy the requirement (for example, recurrence creates tomorrow's task)?
2. **Design check** - does it keep class responsibilities clean (`Task` describes recurrence, `Pet` mutates task lists, `Scheduler` plans)?
3. **Verification check** - run `python -m pytest` and manually run `main.py` for scenario-level confirmation.

If a suggestion passed syntax but violated design boundaries, I modified it instead of accepting it verbatim.

---

## 4. Testing and Verification

**a. What you tested**

I tested five core behaviors:

1. `mark_complete()` flips `completed` from `False` to `True`.
2. Adding a task to a pet increases the task count.
3. `sort_by_time()` returns tasks in chronological HH:MM order.
4. Completing a daily task auto-spawns a new instance due the next day.
5. `detect_conflicts()` flags overlapping/duplicate-time tasks.

These tests are important because they cover the system's reliability pillars: correct state mutation, deterministic ordering, recurrence automation, and safety warnings when a schedule is unrealistic.

**b. Confidence**

Current confidence is **4/5 stars**. The core scheduling workflow is stable and verified by passing tests, but there is still room to broaden boundary coverage.

Next edge cases to test:

1. Tasks with missing `time_of_day` should sort to the end without errors.
2. Non-overlapping boundary times (end equals next start) should not be reported as conflicts.
3. Weekly recurrence should create a task with `due_date = today + 7 days`.
4. Invalid time formats in UI input should be rejected consistently.
5. Multi-pet plans with identical task names should remain correctly attributable by pet.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the separation of concerns in the final design: data behavior in `Task`, ownership and mutation in `Pet`, and planning/filtering/conflict logic in `Scheduler`. That structure made it straightforward to extend features without rewriting the whole system.

**b. What you would improve**

In another iteration, I would redesign task timing around true datetime objects (instead of strings) and add a dedicated conflict-resolution assistant that suggests the best alternative time slots automatically.

**c. Key takeaway**

The biggest takeaway is that AI is strongest when I stay the lead architect. Copilot can generate quickly, but system quality depends on me setting constraints, reviewing each suggestion, and preserving clean boundaries between classes. Using separate chat sessions for design, implementation, testing, and UI helped me stay organized and avoid mixing strategic decisions with tactical edits.
