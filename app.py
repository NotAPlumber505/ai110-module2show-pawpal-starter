import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# ---------------------------------------------------------------------------
# STEP 1 — Create the Owner
# Stores an Owner object in session_state once. Re-clicking updates availability.
# ---------------------------------------------------------------------------
st.subheader("Step 1 — Owner Setup")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Your available time today (minutes)", min_value=1, max_value=480, value=60)

if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

if st.button("Save owner"):
    st.session_state.owner = Owner(name=owner_name, daily_available_minutes=int(available_minutes))
    st.session_state.scheduler = None
    st.success(f"Owner '{owner_name}' saved with {available_minutes} min available.")

if st.session_state.owner:
    st.caption(f"Active owner: **{st.session_state.owner.name}** | {st.session_state.owner.daily_available_minutes} min/day")

st.divider()

# ---------------------------------------------------------------------------
# STEP 2 — Add Pets
# Calls owner.add_pet(pet) to register each pet with the owner.
# get_pets() is called on rerun to display the current list.
# ---------------------------------------------------------------------------
st.subheader("Step 2 — Add a Pet")

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
pet_age = st.number_input("Pet age", min_value=0, max_value=40, value=0)

if st.button("Add pet"):
    if st.session_state.owner is None:
        st.warning("Save an owner first (Step 1).")
    else:
        pet = Pet(name=pet_name, species=species, age=int(pet_age))
        # owner.add_pet() stores the pet AND sets pet.owner = self (back-reference).
        st.session_state.owner.add_pet(pet)
        st.session_state.scheduler = None
        st.success(f"Pet '{pet.name}' added to {st.session_state.owner.name}'s profile.")

# Display registered pets by reading directly from the Owner object.
if st.session_state.owner and st.session_state.owner.get_pets():
    st.write("Registered pets:")
    for p in st.session_state.owner.get_pets():
        st.markdown(f"- **{p.name}** ({p.species})")
elif st.session_state.owner:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# STEP 3 — Schedule a Task
# Calls pet.add_task(task) on the selected Pet object stored inside the Owner.
# ---------------------------------------------------------------------------
st.subheader("Step 3 — Schedule a Task")

if st.session_state.owner and st.session_state.owner.get_pets():
    pet_names = [p.name for p in st.session_state.owner.get_pets()]
    selected_pet_name = st.selectbox("Assign task to", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        category = st.selectbox(
            "Category",
            ["walk", "feeding", "medication", "grooming", "enrichment", "general"],
            index=5,
        )
    with col5:
        time_of_day = st.text_input("Start time (HH:MM)", value="")
    with col6:
        frequency = st.selectbox("Frequency", ["one-time", "daily", "weekly"], index=0)

    recurring = frequency in {"daily", "weekly"}
    frequency_value = "" if frequency == "one-time" else frequency

    if st.button("Add task"):
        # Retrieve the actual Pet object from the owner by matching the selected name.
        target_pet = next(p for p in st.session_state.owner.get_pets() if p.name == selected_pet_name)

        if time_of_day:
            parts = time_of_day.split(":")
            valid_time = (
                len(parts) == 2
                and parts[0].isdigit()
                and parts[1].isdigit()
                and 0 <= int(parts[0]) <= 23
                and 0 <= int(parts[1]) <= 59
                and len(parts[0]) == 2
                and len(parts[1]) == 2
            )
            if not valid_time:
                st.warning("Use HH:MM format for time (for example: 08:30).")
                st.stop()

        task = Task(
            name=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            time_of_day=time_of_day,
            frequency=frequency_value,
            recurring=recurring,
        )
        # pet.add_task() stores the Task inside the Pet's internal task list.
        target_pet.add_task(task)
        st.session_state.scheduler = None
        st.success(f"Task '{task_title}' added to {target_pet.name}.")

    # Show all tasks across all pets.
    all_rows = []
    for p in st.session_state.owner.get_pets():
        for t in p.get_tasks():
            all_rows.append(
                {
                    "pet": p.name,
                    "task": t.name,
                    "minutes": t.duration_minutes,
                    "priority": t.priority,
                    "time": t.time_of_day or "(none)",
                    "frequency": t.frequency or "one-time",
                    "done": "yes" if t.completed else "no",
                }
            )
    if all_rows:
        st.write("All scheduled tasks:")
        st.table(all_rows)
    else:
        st.info("No tasks yet.")
else:
    st.info("Add at least one pet (Step 2) before scheduling tasks.")

st.divider()

# ---------------------------------------------------------------------------
# STEP 4 — Generate the Daily Plan
# Scheduler receives the Owner from session_state and reads all pets/tasks.
# ---------------------------------------------------------------------------
st.subheader("Step 4 — Generate Daily Plan")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Complete Step 1 first.")
    elif not st.session_state.owner.get_pets() or not any(
        p.get_tasks() for p in st.session_state.owner.get_pets()
    ):
        st.warning("Add at least one task (Step 3) before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.generate_plan()
        st.session_state.scheduler = scheduler

if st.session_state.scheduler:
    scheduler = st.session_state.scheduler

    st.subheader("📋 Today's Schedule")

    sort_mode = st.radio(
        "Sort view",
        ["Priority then duration", "Chronological (HH:MM)"],
        horizontal=True,
    )
    pet_filter = st.selectbox(
        "Filter by pet",
        ["All pets"] + [p.name for p in st.session_state.owner.get_pets()],
    )
    status_filter = st.selectbox("Filter by status", ["All", "Incomplete", "Completed"])

    display_tasks = list(scheduler.plan)

    if sort_mode == "Chronological (HH:MM)":
        display_tasks = scheduler.sort_by_time(display_tasks)

    if pet_filter != "All pets":
        pet_ids = {id(t) for t in scheduler.filter_by_pet(pet_filter)}
        display_tasks = [t for t in display_tasks if id(t) in pet_ids]

    if status_filter != "All":
        completed_value = status_filter == "Completed"
        status_ids = {id(t) for t in scheduler.filter_by_status(completed_value)}
        display_tasks = [t for t in display_tasks if id(t) in status_ids]

    task_to_pet = {
        id(task): pet.name
        for pet in st.session_state.owner.get_pets()
        for task in pet.get_tasks()
    }

    if display_tasks:
        rows = []
        for task in display_tasks:
            rows.append(
                {
                    "pet": task_to_pet.get(id(task), "unknown"),
                    "task": task.name,
                    "priority": task.priority,
                    "duration": f"{task.duration_minutes} min",
                    "time": task.time_of_day or "(none)",
                    "status": "completed" if task.completed else "incomplete",
                    "frequency": task.frequency or "one-time",
                }
            )
        st.table(rows)
    else:
        st.warning("No tasks match the current filters.")

    time_used = sum(t.duration_minutes for t in scheduler.plan)
    st.success(f"Time used: {time_used} / {st.session_state.owner.daily_available_minutes} min")

    skipped = scheduler.get_unscheduled_tasks()
    if skipped:
        st.subheader("⏭️ Skipped (didn't fit)")
        skipped_rows = [
            {
                "task": task.name,
                "priority": task.priority,
                "duration": f"{task.duration_minutes} min",
            }
            for task in skipped
        ]
        st.table(skipped_rows)

    warnings = scheduler.detect_conflicts()
    if warnings:
        st.subheader("⚠️ Plan Warnings")
        st.warning(
            "Some tasks overlap or exceed practical limits. Review these before starting your day."
        )
        st.table([{"warning": w} for w in warnings])
        with st.expander("How to resolve warnings"):
            st.markdown(
                """
- Move one of the overlapping tasks by 15-30 minutes.
- Lower duration for optional tasks when your day is full.
- Keep medication and feeding at high priority so they stay scheduled.
"""
            )
