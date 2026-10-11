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

**Priority beats preferred_time, and the clock only moves forward.**

My scheduler sorts by priority first and then assigns times by walking the clock forward from the start time. it never goes backwards and it never fills in a gap. so if a high priority task has a preferred_time later in the morning, that task gets scheduled first and drags the clock forward with it, and everything after it gets pushed back too.

you can see it in my own demo. the morning walk has a preferred_time of 08:00, but Pichu's medication is also high priority and only takes 5 minutes, so medication sorts first. medication wants 09:00, the clock jumps to 09:00, and the walk ends up at 09:15 even though it asked for 08:00. the whole 08:00 to 09:00 hour just sits empty.

I'm leaving it this way on purpose. the thing this app is actually for is making sure the important stuff gets done when the owner is short on time, and it does that correctly: the budget filtering and the priority order both work. the times are more of a suggested order than real appointments. fixing it properly would mean pinning the tasks that have a preferred_time into their slots first and then backfilling the free gaps around them, which is a bigger change than the rest of the scheduler needed, and it would mostly matter for the one case where someone sets a lot of preferred times.

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
