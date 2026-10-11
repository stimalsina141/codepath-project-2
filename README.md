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

Running `python main.py` builds a demo owner with two pets and six tasks, then prints
today's plan twice — once with a normal time budget, and once with a tight one to show
the filtering at work.

```
$ python main.py

Jordan has 2 pets and 6 tasks total.
  - Mochi the dog: 3 task(s), 130 min of care
  - Luna the cat: 3 task(s), 40 min of care

Today's Schedule for Jordan (Tuesday)
Time budget: 75 min | starting at 08:00
------------------------------------------------------------------------
  TIME   TASK            PET      LENGTH  PRIORITY  WHY
------------------------------------------------------------------------
  09:00  Medication      Luna      5 min  high      70 min of budget left
  09:05  Breakfast       Mochi    10 min  high      60 min of budget left
  09:15  Morning walk    Mochi    30 min  high      30 min of budget left
  09:45  Brushing        Luna     15 min  medium    15 min of budget left
------------------------------------------------------------------------
  4 task(s) planned, 60 of 75 min used

Didn't fit today:
  Long hike       Mochi    90 min  low       needs 90 min, only 15 min left

============================================================
What if Jordan only had 25 minutes today?

Today's Schedule for Jordan (Tuesday)
Time budget: 25 min | starting at 08:00
------------------------------------------------------------------------
  TIME   TASK            PET      LENGTH  PRIORITY  WHY
------------------------------------------------------------------------
  09:00  Medication      Luna      5 min  high      20 min of budget left
  09:05  Breakfast       Mochi    10 min  high      10 min of budget left
------------------------------------------------------------------------
  2 task(s) planned, 15 of 25 min used

Didn't fit today:
  Morning walk    Mochi    30 min  high      needs 30 min, only 10 min left
  Brushing        Luna     15 min  medium    needs 15 min, only 10 min left
  Long hike       Mochi    90 min  low       needs 90 min, only 10 min left
```

Note that the weekly nail trim does not appear — it is only due on Mondays, and this
run asks for a Tuesday.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
