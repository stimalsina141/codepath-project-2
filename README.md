# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan their pets' care around
the time they actually have. You tell it your pets, the tasks they need, and how many
minutes you can spare today. It builds a schedule, puts each task on the clock, warns you
about clashes, and explains every decision it made.

## Features

**Priority ranking** — `Scheduler.sort_tasks()` orders tasks by priority (high → medium →
low), then shortest first within a priority so a tight day fits as many as it can. An
unrecognized priority scores 0 and sorts last instead of crashing the plan.

**Budget filtering** — `Scheduler.filter_by_budget()` keeps tasks while the day's minutes
hold out and skips the rest with a reason. It is greedy, not first-failure: a 90-minute
hike that doesn't fit never blocks a 10-minute brushing behind it from using what's left.

**Sorting by time** — `Scheduler.sort_by_time()` returns the plan in clock order rather
than priority order. It sorts on minutes-since-midnight, so a plan running past 24:00
still lists its tasks last, and a hand-typed `9:00` still sorts before `10:00`.

**Gap filling** — `Scheduler.assign_time_slots()` treats tasks with a preferred time as
anchors and places them in clock order. Flexible tasks fill the gaps between anchors if
they finish in time, so no hour sits empty, and whatever is left runs after the last
anchor.

**Conflict warnings** — `Scheduler.detect_conflicts()` compares every pair of timed tasks
and reports three kinds of clash: *same time*, *overlap*, and *late* (pushed more than 15
minutes past its preferred time). It returns warnings rather than raising, so the plan
always shows. Clashes count both within one pet and across pets, since the owner can't be
in two places at once either.

**Daily and weekly recurrence** — completing a repeating task queues a fresh copy:
`"daily"` lands the next day, `"weekly"` seven days out, `"once"` never. The finished task
stays as history, and the copy is held out of plans until its due date.

**Task filtering** — `Scheduler.filter_tasks()` narrows the task list by pet (id or name,
any case) and by done/pending. This drives the app's "Show pet" and "Show status"
dropdowns.

**Explain-the-plan** — every task carries the reason it was chosen, placed, or skipped, so
the schedule justifies itself instead of just listing times.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then run either front end:

```bash
streamlit run app.py   # the interactive app
python main.py         # the terminal demo
```

## Project layout

| File | What it holds |
|------|---------------|
| `pawpal_system.py` | The logic layer: `Owner`, `Pet`, `Task`, `Scheduler`. No Streamlit. |
| `app.py` | The Streamlit UI. Calls into the logic layer and renders what it returns. |
| `main.py` | A terminal demo that walks through every scheduling feature. |
| `tests/test_pawpal.py` | 43 tests over the logic layer. |
| `diagrams/uml_final.mmd` | The class diagram, matching the final code. |

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
python -m pytest

# Quieter output:
python -m pytest -q
```

### What the tests cover

43 tests across the logic layer, grouped by behavior:

| Area | Tests | What it checks |
|------|-------|----------------|
| Task & pet basics | 2 | `mark_complete()` flips a task's status; `add_task()` grows the pet's list. |
| Sorting | 5 | The plan comes back in clock order, not priority order. Flexible tasks fill the gaps before a timed task, or wait if they are too long for the gap. Untimed tasks sort last, and a hand-typed `8:00` still sorts before `10:00`. |
| Filtering | 2 | Narrowing the task list by pet id, by pet name in any case, and by done/pending. |
| Recurrence | 9 | Completing a daily task queues a fresh copy due the next day; a weekly one lands seven days out; a `once` task does not repeat. Reopening a task removes the copy it queued, and a queued copy is not planned before its due date. |
| Conflicts | 7 | Two tasks wanting the same time are flagged, whether they belong to the same pet or to different pets. Overlaps, three-way clashes, and tasks pushed more than 15 minutes late are all reported. Back-to-back tasks are not. |
| Budget | 5 | Tasks that fit the day's minutes are kept and the rest are skipped with a reason. A task too big for the budget does not block a cheaper one behind it. |
| Replanning | 2 | `reset()` wipes the times from the previous plan, so a second run never shows stale slots. |
| Edge cases | 10 | No pets, a pet with no tasks, an unrecognized priority, a priority typed in any case, and malformed times like `""`, `oops`, `8`, `25:00` or `08:70`. |
| Midnight | 1 | A plan running past 24:00 still lists its tasks in chronological order. |

The two tests that matter most are `test_a_task_that_does_not_fit_does_not_block_cheaper_ones`, which guards the
greedy-fill behavior that makes a tight day useful, and `test_replanning_clears_times_from_the_previous_plan`,
which guards the weak spot in the design: the scheduler writes its output onto each `Task`, so a missed reset
would silently leak yesterday's times into today's plan.

### Test run

```
$ python -m pytest
============================= test session starts ==============================
platform darwin -- Python 3.14.8, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/smrititimalsina/Desktop/CodePath/codepath-project-2
plugins: anyio-4.15.1
collected 43 items

tests/test_pawpal.py ...........................................        [100%]

============================== 43 passed in 0.02s ==============================
```

### Confidence level

**★★★★☆ (4 / 5)**

The scheduling logic is well covered and the tests have already earned their keep — writing them surfaced two
real bugs. A plan that ran past midnight listed its tasks out of order, because times were sorted as `"HH:MM"`
strings and a task pushed past 24:00 displays as `00:00`, which sorts before `23:00`. And `parse_time("08:70")`
quietly returned 09:10 instead of rejecting an obvious typo.

A star is held back because the tests only reach the logic layer. `app.py` has no automated coverage, and that
is exactly where the worst bug so far lived: the pet dropdown passed `Pet` objects straight to `st.selectbox`,
which hands back a *copy*, so adding a task mutated a throwaway object. The app said "Added Morning walk" and
the task silently vanished. Every test passed through all of it, because they call `Pet.add_task()` directly
and never go through Streamlit's widget layer. Until the UI is tested too, passing tests say the scheduler is
sound — not that the app is.

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

`Scheduler.sort_by_time(tasks)` returns tasks in clock order, sorting on
`Task.sort_minutes()` — minutes since midnight as a number:

```python
def order(task):
    minutes = task.sort_minutes()
    return (float("inf") if minutes is None else minutes, -task.priority_score(), task.title)

sorted(tasks, key=order)
```

- **Which time it uses:** the assigned slot if the task has one, otherwise its preferred
  time. A hand-typed `"9:00"` is parsed to 540, so it sorts before `"10:00"` (600).
- **Why minutes and not `"HH:MM"` strings:** sorting the display string looks like it
  works, and breaks at midnight. A task pushed past 24:00 shows as `"00:00"`, which
  string-sorts *before* `"23:00"` — so a late-night plan listed its tasks in the wrong
  order. `sort_minutes()` returns the unwrapped number (1440, not 0) and `format_time()`
  wraps only for display.
- **Order of the rest:** tasks with no time sort as infinity and go last. Ties go to
  higher priority, then title.

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

### What you can do in the app

Launch with `streamlit run app.py`.

**Sidebar — your day.** Set your name, how many minutes you can spare today, what time
the day starts, and which weekday to plan for. "Reset everything" clears the session.

**Your pets.** Add a pet with a name, species, breed, and age. Each pet shows its task
count and how many minutes of care it still has pending. 🗑 removes a pet, and its tasks
go with it.

**Care tasks.** Add a task to a chosen pet: title, minutes, priority, category, whether it
repeats daily/weekly/once, and optionally a preferred time. Two dropdowns filter the list
by pet and by done/pending. Each task has a checkbox to tick it off — which also queues
its next occurrence if it repeats — and a 🗑 to delete it. Completed tasks show struck
through, and a queued copy shows its due date.

**Today's schedule.** One button builds the plan. You get a four-metric summary, any
clash warnings, the schedule table, a "didn't fit" table, and a "Why this plan?" panel.
The plan stays on screen and updates live as you tick tasks off.

### An example workflow

1. In the sidebar, set **Minutes free for pet care today** to `60` and **Day** to
   `tuesday`.
2. Add a pet: **Mochi**, dog. Add a second: **Pichu**, cat.
3. Add a task for Mochi — **Walk**, 30 min, high priority, preferred time `08:00`.
4. Add one for Pichu — **Meds**, 5 min, high priority, preferred time `08:00`.
5. Add another for Pichu — **Vet**, 15 min, high, preferred time `08:15`.
6. Add one more for Mochi — **Hike**, 90 min, low priority, no preferred time.
7. Click **Generate schedule**.

The metrics read **Planned 3 · Minutes used 50/60 · Didn't fit 1 · Clashes 3**, and the
schedule comes out in clock order:

| Time | Task | Pet | Minutes | Priority | Why |
|------|------|-----|---------|----------|-----|
| 08:00 | Meds | Pichu | 5 | high | at its preferred time |
| 08:05 | Walk | Mochi | 30 | high | wanted 08:00, pushed back 5 min |
| 08:35 | Vet | Pichu | 15 | high | wanted 08:15, pushed back 20 min |

8. Tick **Hike** off. The plan stays on screen and updates rather than disappearing.

### What the Scheduler is doing here

**Budget filtering.** The 90-minute hike is dropped into "Didn't fit today" with the
reason `needs 90 min, only 25 min left`. The other three tasks total 50 of your 60
minutes.

**Priority ranking, then clock order.** Meds (5 min) is picked before Walk (30 min)
because both are high priority and shortest wins the tie — but the *displayed* plan is in
time order, not pick order.

**Conflict warnings.** Three clashes are reported, grouped by kind and split by whether
you have to act:

> 🚫 **Two things booked for the same moment** — *(red)*
> Pichu's 'Meds' and Mochi's 'Walk' both want 08:00 (different pets)
> *Pick a different time for one of them, or clear its preferred time and let PawPal+ find a free slot.*

> ⏱️ **These run into each other** — *(yellow)*
> Pichu's 'Vet' wants 08:15, but Mochi's 'Walk' runs 08:00–08:30 (different pets)
> *Both are still planned — the later one just waits for the first to finish.*

> 🕒 **Starting later than you asked for** — *(yellow)*
> Pichu's 'Vet' wanted 08:15 but starts at 08:35 (20 min late)

A same-time clash is an error because only you can resolve it. An overlap or a late start
is a warning, because the plan still works — the later task just waits. **The plan never
double-books**: notice Walk moved to 08:05 and Vet to 08:35 rather than stacking.

**Recurrence.** Ticking a daily task off marks it done and immediately adds a fresh copy
due tomorrow, shown greyed with its due date. Unticking removes that copy again.

### Sample CLI output

`python main.py` runs the same features in the terminal, pinned to Tuesday Oct 13 2026 so
the output never changes. This is the conflict section of that run — the full output is
under [Sample Output](#️-sample-output) above:

```
$ python main.py

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

Three behaviors visible in those nine lines: the vet call is pushed from 08:15 to 08:30 so
it doesn't collide with the walk, and the overlap is reported; Brushing has no preferred
time, so it fills the free gap between 08:45 and the 09:00 medication instead of leaving
the slot empty; and the 90-minute hike is dropped for lack of budget, with the shortfall
spelled out.
