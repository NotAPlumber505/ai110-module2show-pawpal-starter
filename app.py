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

if st.button("Save owner"):
    st.session_state.owner = Owner(name=owner_name, daily_available_minutes=int(available_minutes))
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

if st.button("Add pet"):
    if st.session_state.owner is None:
        st.warning("Save an owner first (Step 1).")
    else:
        pet = Pet(name=pet_name, species=species, age=0)
        # owner.add_pet() stores the pet AND sets pet.owner = self (back-reference).
        st.session_state.owner.add_pet(pet)
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

    if st.button("Add task"):
        # Retrieve the actual Pet object from the owner by matching the selected name.
        target_pet = next(p for p in st.session_state.owner.get_pets() if p.name == selected_pet_name)
        task = Task(name=task_title, duration_minutes=int(duration), priority=priority, category="general")
        # pet.add_task() stores the Task inside the Pet's internal task list.
        target_pet.add_task(task)
        st.success(f"Task '{task_title}' added to {target_pet.name}.")

    # Show all tasks across all pets.
    all_rows = []
    for p in st.session_state.owner.get_pets():
        for t in p.get_tasks():
            all_rows.append({"pet": p.name, "task": t.name, "minutes": t.duration_minutes, "priority": t.priority})
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

        st.subheader("📋 Today's Schedule")
        if scheduler.plan:
            for task in scheduler.plan:
                st.success(f"**[{task.priority.upper()}]** {task.name} — {task.duration_minutes} min")
            time_used = sum(t.duration_minutes for t in scheduler.plan)
            st.info(f"Time used: {time_used} / {st.session_state.owner.daily_available_minutes} min")
        else:
            st.warning("No tasks fit within your available time.")

        skipped = scheduler.get_unscheduled_tasks()
        if skipped:
            st.subheader("⏭️ Skipped (didn't fit)")
            for task in skipped:
                st.error(f"{task.name} — {task.duration_minutes} min")
