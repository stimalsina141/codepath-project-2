# PawPal+ Project Reflection

## 1. System Design

The three core actions that a user should be able to perform are:
a. adding a pet, with owner details and pet info
b. schedule a task for the pet (e.g.: grooming, walking, medications etc)
c. see the daily schedule, list of tasks, priority tasks, etc.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

I started with four classes: Owner, Pet, Task, and Scheduler.

- **Owner** is the person using the app. it holds their name, email, and how many minutes they have free for pet care that day. it also keeps the list of pets they own.
- **Pet** is the animal being taken care of. it holds the basic info like name, species, breed, age, and energy level, and it keeps its own list of tasks.
- **Task** is one thing that needs to get done (e.g.: a walk, feeding, meds). it holds the title, how long it takes, and the priority (low, medium, high). it also knows its category and whether it repeats daily or weekly.
- **Scheduler** is the part that actually builds the plan. it takes the owner and their time budget, sorts the tasks by priority, drops the ones that don't fit, and gives each one a time. it also keeps a list of what got skipped, so the app can explain the plan instead of just showing it.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, it changed a few times.

**1. wake_time and sleep_time became available_minutes.** this one happened while I was still drawing the diagram. at first I gave Owner a wake_time and a sleep_time so the scheduler would know what window of the day to work in. but that got complicated fast, and it also assumed the owner spends their whole day on the pet, which isn't true. so I took both out and replaced them with available_minutes, which is just how many minutes they actually want to spend on pet care. the scheduler still needs a clock to start from, so that became start_time on Scheduler instead.

After I wrote the class skeletons I had AI review the file and point out anything missing. a few things it caught were real problems, so I fixed them:

**2. there was nowhere to store the time the scheduler picks.** I had a preferred_time on Task, but that is the time the owner *wants*, not the time the scheduler actually assigns. so assign_time_slots had nothing to write its answer to. I added scheduled_minutes to Task to hold the real slot.

**3. the plan lost track of which pet a task belonged to.** the scheduler flattens all the pets' tasks into one list, and once that happens there was no way to tell whose task it was. that breaks the output if someone has more than one pet. I added pet_id to Task, and Pet.add_task sets it automatically so I don't have to pass it twice.

**4. the pipeline was missing its first step.** sort_tasks took a list of tasks but nothing actually built that list. I added collect_tasks to gather the pending tasks from all the pets first.

**5. I moved the "why" onto the task itself.** I originally had a separate reasons list on Scheduler sitting next to the planned and skipped lists. the problem is nothing connects a reason to the task it's about, and the lists can easily get out of sync. now each Task has its own reason field.

**6. times are ints inside, strings only for display.** I was storing times like "08:00" as strings, which means every time you add 30 minutes you have to pull the string apart and put it back together. that's easy to get wrong. now the math happens in minutes since midnight and I only format it as "08:00" when it gets shown.

The tradeoff with #2 and #3 is that Task now holds both input and output, so Scheduler.reset() has to go clear those fields off every task before replanning. if it forgets, old times leak into the next plan. I chose this over adding a fifth class because I wanted to keep the four classes from my original design.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Conflicts get a warning, not a fix. Whoever asked for the earlier time keeps it, even if it's lower priority.**

when two tasks want overlapping times, my scheduler doesn't try to work out the best arrangement. it places timed tasks in clock order, the first one keeps its slot, and the later one just gets pushed back until the first is done. then detect_conflicts adds a warning like "Overlap: Pichu's 'Vet call' wants 08:15, but Mochi's 'Morning walk' runs 08:00–08:30 (different pets)" and the plan still shows. it never crashes or refuses to make a plan.

the catch is that priority only decides *which* tasks make it into the day, not *who wins* a time clash. if a low priority 60 min game of fetch wants 08:00 and high priority meds want 08:30, fetch keeps 08:00 and the meds get pushed to 09:00. the owner gets an overlap warning and a "30 min late" warning, but the scheduler doesn't move fetch out of the way on its own.

(this replaced an earlier, worse version of the same problem. at first the scheduler assigned times in priority order, so a short high priority task at 09:00 dragged the clock forward and the 08:00 walk ended up at 09:15 with the whole 08:00 hour empty. I fixed that by placing timed tasks in clock order and filling the gaps with flexible ones.)

I think this is reasonable for a pet owner. preferred times are usually things only the owner knows how to trade off. maybe the vet call can't move but the walk can, or the meds have a 30 min window and fetch doesn't. a scheduler that quietly reshuffled things based on priority could move something that really was fixed, which is worse than showing a clear warning and letting the owner decide. it also keeps the logic simple and predictable: what you asked for, in time order, with every clash called out. the downside is that the owner has to read the warnings and fix them by hand.

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
