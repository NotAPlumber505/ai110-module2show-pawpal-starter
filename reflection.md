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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
