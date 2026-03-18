from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", daily_available_minutes=120)

dog = Pet(name="Biscuit", species="Dog", age=3)
cat = Pet(name="Luna", species="Cat", age=5)

owner.add_pet(dog)
owner.add_pet(cat)

# Tasks added OUT OF ORDER by time_of_day to prove sort_by_time() works
dog.add_task(Task(name="Evening walk",      duration_minutes=25, priority="medium", category="walk",
                  time_of_day="17:30", frequency="daily"))
dog.add_task(Task(name="Flea medication",   duration_minutes=5,  priority="high",   category="medication",
                  time_of_day="08:00"))
dog.add_task(Task(name="Morning walk",      duration_minutes=30, priority="high",   category="walk",
                  time_of_day="07:30", frequency="daily"))
dog.add_task(Task(name="Fetch in backyard", duration_minutes=20, priority="medium", category="enrichment",
                  time_of_day="15:00"))
# Deliberate time-overlap: Vet call (07:45) overlaps Morning walk (07:30-08:00)
dog.add_task(Task(name="Vet check-in call", duration_minutes=20, priority="high",   category="medication",
                  time_of_day="07:45"))

cat.add_task(Task(name="Afternoon play",    duration_minutes=15, priority="low",    category="enrichment",
                  time_of_day="13:00"))
cat.add_task(Task(name="Feeding",           duration_minutes=10, priority="high",   category="feeding",
                  time_of_day="08:30", frequency="daily"))
cat.add_task(Task(name="Brush coat",        duration_minutes=15, priority="medium", category="grooming",
                  time_of_day="09:00"))

# ============================================================
# GENERATE PLAN (priority -> shortest-first within tier)
# ============================================================
scheduler = Scheduler(owner)
scheduler.generate_plan()

print("=" * 62)
print("  TODAY'S PLAN  (priority -> shortest-first within tier)")
print("=" * 62)
print(scheduler.explain_plan())

# ============================================================
# FEATURE: sort_by_time() - tasks were added out of order;
#           this restores chronological clock order
# ============================================================
print()
print("=" * 62)
print("  SCHEDULE SORTED BY TIME OF DAY")
print("=" * 62)
for task in scheduler.sort_by_time():
    tl = f"@ {task.time_of_day}  " if task.time_of_day else "(no time)  "
    print(f"  {tl}[{task.priority.upper()}] {task.name} - {task.duration_minutes} min")

# ============================================================
# FEATURE: filter_by_pet() and filter_by_status()
# ============================================================
print()
print("=" * 62)
print("  FILTER: Biscuit's scheduled tasks only")
print("=" * 62)
for task in scheduler.filter_by_pet("Biscuit"):
    print(f"  * {task.name} ({task.duration_minutes} min, {task.priority})")

print()
print("  FILTER: Incomplete tasks in today's plan")
print("-" * 62)
for task in scheduler.filter_by_status(completed=False):
    freq = f"  [{task.frequency}]" if task.frequency else ""
    print(f"  * {task.name}{freq}")

# ============================================================
# FEATURE: frequency + spawn_next() via timedelta
#   complete_task() marks done AND auto-creates the next instance
# ============================================================
print()
print("=" * 62)
print("  FREQUENCY / AUTO-SPAWN DEMO  (using timedelta)")
print("=" * 62)
print("  Completing 'Morning walk' (frequency=daily) for Biscuit...")
next_task = dog.complete_task("Morning walk")
if next_task:
    print(f"  -> Next occurrence: '{next_task.name}'  due {next_task.due_date}")

print("  Completing 'Feeding' (frequency=daily) for Luna...")
next_task = cat.complete_task("Feeding")
if next_task:
    print(f"  -> Next occurrence: '{next_task.name}'  due {next_task.due_date}")

# ============================================================
# FEATURE: detect_conflicts() - duplicate names + time overlaps
# ============================================================
print()
print("=" * 62)
print("  CONFLICT DETECTION  (includes time-slot overlap)")
print("=" * 62)
scheduler.generate_plan()   # refresh plan so timed tasks are in self.plan
conflicts = scheduler.detect_conflicts()
if conflicts:
    for w in conflicts:
        print(f"  !  {w}")
else:
    print("  No conflicts detected.")

# --- Pet profiles ---
print()
print("=" * 62)
print("  PET PROFILES")
print("=" * 62)
for pet in owner.get_pets():
    print(" ", pet.get_profile())
