import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def get_owner() -> Owner:
    """Return this session's Owner, building it only on the very first run.

    Streamlit re-runs this whole script on every interaction. Without the
    "already in session_state?" check, the Owner would be rebuilt empty each
    time and every pet and task would be lost.
    """
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(owner_id="owner-1", name="Jordan")
    return st.session_state.owner


def next_id(prefix: str) -> str:
    """Hand out a unique id like "pet-1" or "task-3", counting per prefix."""
    key = f"{prefix}_counter"
    st.session_state[key] = st.session_state.get(key, 0) + 1
    return f"{prefix}-{st.session_state[key]}"


owner = get_owner()

st.title("🐾 PawPal+")
st.caption("Plan your pets' care around the time you actually have today.")


# --- Owner settings -------------------------------------------------------
# These write straight onto the Owner object held in session_state, so each
# edit survives the rerun it triggers.

with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Your name", value=owner.name)
    owner.available_minutes = st.number_input(
        "Minutes free for pet care today",
        min_value=0,
        max_value=600,
        value=owner.available_minutes,
        step=5,
    )
    start_time = st.text_input("Start the day at", value="08:00")
    day = st.selectbox("Day", WEEKDAYS, index=0)

    st.divider()
    if st.button("Reset everything"):
        st.session_state.clear()
        st.rerun()


# --- Add a pet ------------------------------------------------------------
# Owner.add_pet() is the method that handles the submitted data.

st.subheader("Your pets")

with st.form("add_pet", clear_on_submit=True):
    st.markdown("**Add a pet**")
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Name", value="")
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col2:
        breed = st.text_input("Breed", value="")
        age = st.number_input("Age", min_value=0, max_value=40, value=0)

    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.warning("Give your pet a name first.")
        else:
            owner.add_pet(
                Pet(
                    pet_id=next_id("pet"),
                    name=pet_name.strip(),
                    species=species,
                    breed=breed.strip(),
                    age=int(age),
                )
            )
            st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    # Removing a pet takes its tasks with it, since the tasks live on the Pet.
    pet_to_remove = None

    for pet in owner.pets:
        label_col, delete_col = st.columns([11, 1])

        with label_col:
            label = f"{pet.name} — {pet.species}"
            if pet.breed:
                label += f" ({pet.breed})"
            st.write(
                f"**{label}** · {len(pet.tasks)} task(s) · "
                f"{pet.total_duration()} min of care left"
            )

        with delete_col:
            if st.button("🗑", key=f"del-{pet.pet_id}", help=f"Remove {pet.name}"):
                pet_to_remove = pet.pet_id

    if pet_to_remove:
        owner.remove_pet(pet_to_remove)
        st.rerun()
else:
    st.info("No pets yet. Add one above to get started.")


# --- Add a task -----------------------------------------------------------
# Pet.add_task() handles this one: it appends the Task and stamps its pet_id.

st.divider()
st.subheader("Care tasks")

if not owner.pets:
    st.caption("Add a pet first, then you can give them tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        st.markdown("**Add a task**")

        # Pick by pet_id, not by passing the Pet itself. Streamlit stores a
        # widget's value in session_state, and what comes back is a *copy* of
        # the object — mutating it would update a throwaway, not the real pet.
        chosen_pet_id = st.selectbox(
            "Which pet?",
            options=[pet.pet_id for pet in owner.pets],
            format_func=lambda pet_id: owner.get_pet(pet_id).name,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task", value="")
        with col2:
            duration = st.number_input("Minutes", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])

        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox(
                "Category",
                ["general", "exercise", "feeding", "health", "grooming", "enrichment"],
            )
            recurrence = st.selectbox("Repeats", ["daily", "weekly"])
        with col5:
            wants_time = st.checkbox("Has a preferred time")
            preferred = st.text_input("Preferred time (HH:MM)", value="08:00")
            days = st.multiselect("On which days?", WEEKDAYS)

        if st.form_submit_button("Add task"):
            # Look the pet up by id so we attach the task to the live object.
            pet_choice = owner.get_pet(chosen_pet_id)

            if not task_title.strip():
                st.warning("Give the task a title first.")
            elif pet_choice is None:
                st.warning("That pet is no longer around. Pick another one.")
            else:
                pet_choice.add_task(
                    Task(
                        task_id=next_id("task"),
                        title=task_title.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        category=category,
                        preferred_time=preferred if wants_time else None,
                        recurrence=recurrence,
                        days=days,
                    )
                )
                st.success(f"Added '{task_title.strip()}' for {pet_choice.name}.")

    # Tick a task off with Task.mark_complete() / Task.reopen(), or remove it
    # with Pet.remove_task(). Deletions are collected and applied after the
    # loop, so the list is never mutated while it is being iterated.
    pending_deletes: list[tuple[Pet, str]] = []

    for pet in owner.pets:
        if not pet.tasks:
            continue

        st.markdown(f"**{pet.name}**")
        for task in pet.tasks:
            done_col, label_col, delete_col = st.columns([1, 10, 1])

            with done_col:
                is_done = st.checkbox(
                    "Done",
                    value=task.completed,
                    key=f"done-{task.task_id}",
                    label_visibility="collapsed",
                )
                if is_done and not task.completed:
                    task.mark_complete()
                elif not is_done and task.completed:
                    task.reopen()

            with label_col:
                details = (
                    f"{task.duration_minutes} min · {task.priority} · "
                    f"{task.category} · {task.recurrence}"
                )
                if task.completed:
                    st.markdown(f"~~{task.title}~~  \n:gray[{details}]")
                else:
                    st.markdown(f"{task.title}  \n:gray[{details}]")

            with delete_col:
                if st.button("🗑", key=f"del-{task.task_id}", help=f"Delete {task.title}"):
                    pending_deletes.append((pet, task.task_id))

    for pet, task_id in pending_deletes:
        pet.remove_task(task_id)
    if pending_deletes:
        st.rerun()


# --- Build the schedule ---------------------------------------------------
# Scheduler does the real work; the UI just renders what it returns.

st.divider()
st.subheader("Today's schedule")

if st.button("Generate schedule", type="primary", disabled=not owner.pets):
    try:
        scheduler = Scheduler(owner, start_time=start_time)
        plan = scheduler.generate_plan(day=day)
    except ValueError as error:
        st.error(f"Couldn't build a schedule: {error}")
    else:
        st.caption(
            f"{owner.available_minutes} min budget, starting at {start_time}, for {day.title()}."
        )

        if plan:
            used = sum(task.duration_minutes for task in plan)
            st.table(
                [
                    {
                        "Time": task.scheduled_time(),
                        "Task": task.title,
                        "Pet": pet.name if (pet := scheduler.pet_for(task)) else "—",
                        "Minutes": task.duration_minutes,
                        "Priority": task.priority,
                        "Why": task.reason,
                    }
                    for task in plan
                ]
            )
            st.success(
                f"{len(plan)} task(s) planned, {used} of {owner.available_minutes} min used."
            )
        else:
            st.warning("Nothing fit in today's budget.")

        skipped = scheduler.get_skipped_tasks()
        if skipped:
            st.markdown("**Didn't fit today**")
            st.table(
                [
                    {
                        "Task": task.title,
                        "Pet": pet.name if (pet := scheduler.pet_for(task)) else "—",
                        "Minutes": task.duration_minutes,
                        "Priority": task.priority,
                        "Why": task.reason,
                    }
                    for task in skipped
                ]
            )

        with st.expander("Why this plan?"):
            for line in scheduler.explain_plan():
                st.write(line)
