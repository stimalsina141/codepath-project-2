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

## 🖥️ Sample Output

Running `python main.py` builds a demo owner with two pets and six tasks (deliberately
added out of time order), then walks through each scheduling feature: sorting and
filtering the task list, a normal plan, a tight budget, filtering, completing a
recurring task, and a conflict warning. The demo is pinned to Tuesday Oct 13, 2026 so
the output is the same whenever it runs.

```
$ python main.py

Jordan has 2 pets and 6 tasks total.
  - Mochi the dog: 3 task(s), 130 min of care
  - Pichu the cat: 3 task(s), 40 min of care

============================================================
Sorting and filtering

In the order they were added:
  --:--  Long hike     Mochi  pending
  08:45  Breakfast     Mochi  pending
  08:00  Morning walk  Mochi  pending
  09:00  Medication    Pichu  pending
  --:--  Nail trim     Pichu  pending
  --:--  Brushing      Pichu  pending

Sorted by time:
  08:00  Morning walk  Mochi  pending
  08:45  Breakfast     Mochi  pending
  09:00  Medication    Pichu  pending
  --:--  Brushing      Pichu  pending
  --:--  Long hike     Mochi  pending
  --:--  Nail trim     Pichu  pending

Just Mochi, by time:
  08:00  Morning walk  Mochi  pending
  08:45  Breakfast     Mochi  pending
  --:--  Long hike     Mochi  pending

(Breakfast marked done)

Still pending:
  08:00  Morning walk  Mochi  pending
  09:00  Medication    Pichu  pending
  --:--  Brushing      Pichu  pending
  --:--  Long hike     Mochi  pending
  --:--  Nail trim     Pichu  pending

Done:
  08:45  Breakfast     Mochi  done

Pichu's pending tasks:
  09:00  Medication    Pichu  pending
  --:--  Brushing      Pichu  pending
  --:--  Nail trim     Pichu  pending

============================================================

Today's Schedule for Jordan (Tuesday Oct 13)
Time budget: 75 min | starting at 08:00
------------------------------------------------------------------------
  TIME   TASK            PET      LENGTH  PRIORITY  WHY
------------------------------------------------------------------------
  08:00  Morning walk    Mochi    30 min  high      at its preferred time
  08:30  Brushing        Pichu    15 min  medium    flexible, fills the gap before 08:45
  08:45  Breakfast       Mochi    10 min  high      at its preferred time
  09:00  Medication      Pichu     5 min  high      at its preferred time
------------------------------------------------------------------------
  4 task(s) planned, 60 of 75 min used

Didn't fit today:
  Long hike       Mochi    90 min  low       needs 90 min, only 15 min left

============================================================
What if Jordan only had 25 minutes today?

Today's Schedule for Jordan (Tuesday Oct 13)
Time budget: 25 min | starting at 08:00
------------------------------------------------------------------------
  TIME   TASK            PET      LENGTH  PRIORITY  WHY
------------------------------------------------------------------------
  08:45  Breakfast       Mochi    10 min  high      at its preferred time
  09:00  Medication      Pichu     5 min  high      at its preferred time
------------------------------------------------------------------------
  2 task(s) planned, 15 of 25 min used

Didn't fit today:
  Morning walk    Mochi    30 min  high      needs 30 min, only 10 min left
  Brushing        Pichu    15 min  medium    needs 15 min, only 10 min left
  Long hike       Mochi    90 min  low       needs 90 min, only 10 min left

============================================================
Recurring tasks, completed on Tuesday Oct 13:
  Breakfast (daily) done -> next one due Wednesday Oct 14
  Nail trim (weekly) done -> next one due Tuesday Oct 20

All tasks now:
  08:00  Morning walk  Mochi  pending
  08:45  Breakfast     Mochi  done
  08:45  Breakfast     Mochi  pending, due Oct 14
  09:00  Medication    Pichu  pending
  --:--  Brushing      Pichu  pending
  --:--  Long hike     Mochi  pending
  --:--  Nail trim     Pichu  done
  --:--  Nail trim     Pichu  pending, due Oct 20

============================================================
Pichu's vet call is booked at 08:15, in the middle of Mochi's walk:

Today's Schedule for Jordan (Tuesday Oct 13)
Time budget: 75 min | starting at 08:00
------------------------------------------------------------------------
  TIME   TASK            PET      LENGTH  PRIORITY  WHY
------------------------------------------------------------------------
  08:00  Morning walk    Mochi    30 min  high      at its preferred time
  08:30  Vet call        Pichu    15 min  high      wanted 08:15, pushed back 15 min
  08:45  Brushing        Pichu    15 min  medium    flexible, fills the gap before 09:00
  09:00  Medication      Pichu     5 min  high      at its preferred time
------------------------------------------------------------------------
  4 task(s) planned, 65 of 75 min used
  ! Overlap: Pichu's 'Vet call' wants 08:15, but Mochi's 'Morning walk' runs 08:00–08:30 (different pets)

Didn't fit today:
  Long hike       Mochi    90 min  low       needs 90 min, only 10 min left
```

Things to notice:

- `sort_by_time()` turns the out-of-order list into clock order. Medication was typed
  as `9:00` but still sorts after `08:45`, and untimed tasks go last.
- `filter_tasks(pet_name=..., completed=...)` narrows the list by pet name (any case)
  and/or done/pending status.
- The plan reads in clock order. Brushing has no preferred time, so it slots into the
  free gap between the 08:30 end of the walk and the 08:45 breakfast.
- The weekly nail trim does not appear: it is only due on Mondays.
- `Scheduler.mark_task_complete()` keeps a finished task as "done" and queues a fresh
  copy: daily Breakfast comes back the next day (+1 day), weekly Nail trim in 7 days.
- The 08:15 vet call is moved to 08:30 so nothing is double-booked, and the overlap is
  reported as a warning.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
$ pytest -q
.................                                                        [100%]
25 passed
```

## 📐 Smarter Scheduling

`Scheduler.generate_plan()` runs every feature below in one pass:

1. **Collect** the pending tasks due today (`collect_tasks`, which uses `Task.is_due_today`).
2. **Rank** them by priority (`sort_tasks`).
3. **Keep** the ones that fit the time budget (`filter_by_budget`).
4. **Place** them on the clock (`assign_time_slots`, which uses `sort_by_time`).
5. **Check** the result for clashes (`detect_conflicts`).

| Feature | Main method | Supporting methods |
|---------|-------------|--------------------|
| Sorting | `Scheduler.sort_by_time()` | `Scheduler.sort_tasks()`, `Scheduler.assign_time_slots()`, `Task.time_string()` |
| Filtering | `Scheduler.filter_tasks()` | `Scheduler.filter_by_budget()` |
| Conflict detection | `Scheduler.detect_conflicts()` | `Scheduler.get_conflicts()` |
| Recurring tasks | `Scheduler.mark_task_complete()` | `Task.next_occurrence()`, `Pet.complete_task()`, `Pet.reopen_task()`, `Task.is_due_today()` |

### Sorting by time

`Scheduler.sort_by_time(tasks)` returns tasks in clock order. It calls `sorted()` with a
lambda key built from each task's `"HH:MM"` string:

```python
sorted(tasks, key=lambda task: (task.time_string() or "99:99", -task.priority_score(), task.title))
```

- **Why strings work:** zero-padded `"HH:MM"` strings sort the same as the times they
  stand for (`"08:45" < "09:00" < "13:30"`). `Task.time_string()` pads a hand-typed
  `"9:00"` to `"09:00"` so it doesn't sort after `"10:00"`.
- **Which time it uses:** the assigned slot if the task has one, otherwise its preferred
  time.
- **Order of the rest:** tasks with no time get `"99:99"` and go last. Ties go to higher
  priority, then title.

Two kinds of sorting work together in the plan. `sort_tasks()` ranks by priority (then
shortest first) to decide **which** tasks make the cut. `assign_time_slots()` decides
**when** they run: it places tasks with a preferred time in clock order and fills the
gaps between them with flexible tasks, so no hour sits empty.

### Filtering

`Scheduler.filter_tasks(pet_id=None, completed=None, pet_name=None)` narrows the owner's
task list:

- by pet, using either its id or its name (any case)
- by status: `completed=False` for pending, `completed=True` for done

Filters combine, e.g. `filter_tasks(pet_name="Pichu", completed=False)`. Any filter left as
`None` is ignored, so `filter_tasks()` returns everything. The Streamlit app's "Show pet"
and "Show status" dropdowns use this method.

`Scheduler.filter_by_budget(tasks)` is the planning-time filter. It walks the
priority-ranked list and keeps each task that still fits the minutes left. A task that
doesn't fit is skipped with a reason, and the walk continues, so a shorter task further
down can still use the leftover time.

### Conflict detection

`Scheduler.detect_conflicts(tasks)` is deliberately lightweight. It returns a list of
warning strings and never raises, so the plan always shows. `generate_plan()` stores the
warnings, and `Scheduler.get_conflicts()` returns them.

- **Same time:** two tasks want exactly the same start time.
- **Overlap:** a task wants to start while another task is still running.
- **Late:** a task ended up starting more than 15 minutes after its preferred time
  (`LATE_TOLERANCE_MINUTES`).

Every pair of timed tasks is compared with `itertools.combinations`, so no clash is
missed. A day only has a handful of tasks, so this stays cheap. Clashes count whether
they're for the **same pet** (a pet can't do two things at once) or **different pets** (the
owner can't be in two places at once). Each warning names both pets and says which case
it is:

```
Same time: Mochi's 'Breakfast' and Mochi's 'Walk' both want 08:00 (same pet)
Overlap: Pichu's 'Vet call' wants 08:15, but Mochi's 'Morning walk' runs 08:00–08:30 (different pets)
```

The plan itself never double-books: the later task is pushed back until the earlier one
ends. See `reflection.md` section 2b for the tradeoff this makes.

### Recurring tasks

`Scheduler.mark_task_complete(task, on=None)` marks a task done and, if it repeats,
creates its next occurrence automatically. You only pass the task; the scheduler finds
its pet.

| `recurrence` | Next copy is due |
|--------------|------------------|
| `"daily"` | `on + timedelta(days=1)` |
| `"weekly"` | `on + timedelta(days=7)` |
| `"once"` | no copy |

`on` defaults to today.

- `Task.next_occurrence()` builds the copy, with a new id like `t2@2026-10-14`.
- `Pet.complete_task()` adds the copy to the pet's task list.
- The finished task stays marked "done" as history.
- `Task.is_due_today()` keeps a copy out of plans until its `due_date`, and limits
  weekly tasks to the weekdays in `days`.
- `Pet.reopen_task()` undoes a completion and removes the copy it queued, so ticking and
  unticking a task in the app doesn't create duplicates.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
