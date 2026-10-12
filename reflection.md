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

My scheduler looks at five things:

1. **the time budget** — available_minutes, how many minutes the owner actually has today.
2. **priority** — high, medium, low, which decides what gets cut when the budget runs out.
3. **preferred times** — a task can ask for a specific time, like meds at 09:00.
4. **recurrence and due dates** — daily, weekly or once, and whether a queued copy is due yet.
5. **completion status** — anything already ticked off is left out of the plan.

I ranked them by what the app is actually for. the whole point is helping someone who is short on time, so the **time budget is the hard limit** — it's the one thing you cannot negotiate, you can't make more minutes exist. everything else is a way of deciding how to spend them.

**priority comes second** because that's what answers "if I can't do everything, what do I drop?". inside the same priority I sort shortest first, so a tight day fits as many tasks as it can instead of one big one.

**preferred times come third** and they're soft. they decide *when* things happen, not *whether* they happen. a task with a preferred time gets placed at that time if it can, and pushed back if something else is already there.

**recurrence and completion are filters** more than constraints. they just decide what's even on today's list before the real scheduling starts.

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

I used AI at every phase, but for different jobs each time: brainstorming the classes, reviewing my skeleton before I wrote any logic, writing the scheduling methods, driving the Streamlit app to find bugs, and writing the test suite.

The features that actually mattered for building the scheduler:

**Being able to run my code, not just write it.** this was by far the most useful thing. the worst bug in my whole project was in app.py: I passed Pet objects straight into st.selectbox, and Streamlit gives you back a *copy* of a widget's value, not the original object. so pet.add_task() ran on a throwaway, the app said "Added Morning walk", and the task vanished. nothing about the code looked wrong. it was only found by actually driving the app and checking whether the task was really there afterwards. an assistant that only reads code would never have caught that.

**Reviewing the design before the logic existed.** after I wrote the class stubs I asked "what relationships or bottlenecks are missing here?" instead of "write this for me". that one question found four real holes at a point where they were cheap to fix — there was nowhere to store the time the scheduler picks, the plan lost track of which pet a task belonged to, the pipeline had no first step, and the reasons list wasn't tied to the tasks it described. fixing those in a diagram took minutes. fixing them after writing all the scheduling logic would have meant rewriting it.

**Cross-checking the docs against the real code.** at the end I had it compare every method in pawpal_system.py against my UML diagram in both directions — nothing in the code missing from the diagram, nothing in the diagram that doesn't exist. that's the kind of boring check I would definitely have skipped by hand, and my diagram would have quietly gone stale.

The prompts that worked best were the ones that asked it to **find problems rather than produce code**: "what's missing", "what would break", "is this still accurate". asking for code gets you code whether or not the code is a good idea.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

The clearest one was about where to store the scheduler's output.

When my skeleton got reviewed, the problem it found was real: assign_time_slots had nowhere to write the time it calculated, and the plan couldn't tell which pet a task belonged to. but the fix it recommended was to add a fifth class, a ScheduledItem that wraps a Task with its start time, pet and reason. the argument for it was good — Task stays pure input data, reset() becomes one line, and each reason is attached to the thing it explains.

I said no and put the fields on Task instead. two reasons. first, I'd designed four classes on purpose and I didn't want a fifth appearing because of an implementation detail. second, I could actually explain the four-class version to someone, and a wrapper object sitting between the scheduler and the task felt like something I'd have trouble defending.

What made it a real decision instead of just stubbornness is that I understood the cost before I picked. putting output on Task means Task holds two different kinds of thing at once — what the owner typed in, and what the scheduler decided — and it means reset() has to walk every task and clear those fields before replanning. if it ever misses one, yesterday's times leak into today's plan and nothing warns you.

So I made that the thing I verified. there's a test called test_replanning_clears_times_from_the_previous_plan that builds a plan, replans with a smaller budget, and checks that a task dropped from the second plan has its time wiped. that's the exact failure my choice risks, so it's the one I pinned down with a test.

More generally, the way I checked AI suggestions was to not take "it works" as an answer. I ran main.py, I drove the Streamlit app and checked the objects afterwards, and I wrote tests for the behaviors I was told were fine. that's how two more bugs turned up that nobody had spotted: a plan running past midnight listed its tasks in the wrong order because times were being sorted as "HH:MM" strings and 00:00 sorts before 23:00, and parse_time("08:70") quietly returned 09:10 instead of rejecting an obvious typo.

**c. Working in separate sessions**

- How did using separate chat sessions for different phases help you stay organized?

I used a different chat for the design, the implementation, and the testing instead of one long conversation, and it helped more than I expected.

Each session only knew about the job in front of it. the design chat was about classes and responsibilities and never got tangled up in test fixtures. the testing chat started from the finished code and asked "what isn't covered here", which is a different question from "how should this work" and I don't think I'd have asked it properly in the middle of writing the scheduler. when I came back to a phase later I could reread just that chat instead of scrolling past everything else.

The useful side effect was that a new session didn't know the decisions I'd made earlier, so I had to restate them. explaining out loud why Task holds the scheduler's output, or why available_minutes replaced wake_time, made me check whether I actually still believed it. a couple of times I didn't, and that's where the design got better.

The cost is that nothing carries over automatically. the testing session didn't know the tradeoffs I'd already accepted, so some of what it flagged was stuff I'd decided on purpose. that's a fair trade for the focus, but it means the documentation has to be good enough to catch a session up — which is part of why the README and the UML got as detailed as they did.

**d. Being the lead architect**

- What did you learn about leading the work when collaborating with powerful AI tools?

The main thing is that **the AI is very good at answering the question you asked, and has no opinion about whether it was the right question.** it will happily build whatever you describe. deciding what to build, and what not to, stayed my job the whole time.

The ScheduledItem moment is the clearest example. the suggestion wasn't wrong — by most measures it was the cleaner design. but "cleaner" isn't the only thing that matters. I needed a system I could explain and defend, and keeping four classes with a cost I understood beat five classes I'd have to justify. the AI couldn't make that call because it isn't the one who has to stand behind the design.

I also learned that **the architect's real work is deciding what to verify.** AI generates code much faster than I can read it carefully, so reviewing every line isn't realistic. what is realistic is knowing where my design is weakest and testing exactly there. I knew putting scheduler output on Task made replanning fragile, so that got a test. that's a different skill from writing code, and it's the one that actually kept the project honest.

And **"the tests pass" is not the same as "the app works."** all 43 of my tests passed straight through the Streamlit copy bug, because they call Pet.add_task() directly and never touch a widget. passing tests only tell you about the layer they cover. knowing which layer that is, and what's still unguarded, is the architect's problem, not the assistant's.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

43 tests over the logic layer, grouped into eight areas:

- **task and pet basics (2)** — mark_complete() flips a task's status, and add_task() grows the pet's list.
- **sorting (5)** — the plan comes back in clock order, not priority order. flexible tasks fill the gap before a timed task, or wait if they're too long for it. untimed tasks go last, and a hand-typed "8:00" still sorts before "10:00".
- **filtering (2)** — narrowing the task list by pet id, by pet name in any case, and by done/pending.
- **recurrence (9)** — completing a daily task queues a copy due tomorrow, weekly lands 7 days out, "once" doesn't repeat. reopening removes the copy it queued, and a queued copy isn't planned before its due date.
- **conflicts (7)** — same-time clashes for one pet and across pets, overlaps, three-way clashes, and tasks starting more than 15 min late. back-to-back tasks are checked *not* to be flagged.
- **budget (5)** — tasks that fit are kept, the rest are skipped with a reason, and a task too big for the budget doesn't block a cheaper one behind it.
- **replanning (2)** — reset() wipes the previous plan's times off every task.
- **edge cases (10)** — no pets, a pet with no tasks, an unrecognized priority, a priority typed in any case, and bad times like "", "oops", "8", "25:00", "08:70".
- **midnight (1)** — a plan running past 24:00 still lists its tasks in the right order.

The two that matter most are the greedy-fill one and the replanning one. **greedy fill** is what makes a tight day actually useful — skipping a 90 min hike must not stop a 10 min brushing from using the leftover minutes — and it's easy to break by accident with a `break` instead of a `continue`. **replanning** is the weak point of my design, since the scheduler writes its output onto each Task, so that test guards the exact thing my four-class choice risks.

The conflict and recurrence tests matter because those are the features with the most branches. "weekly, but only on Mondays, and not until its due date" has several ways to be subtly wrong, and none of them would crash — you'd just get a plan that's quietly incorrect.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**4 out of 5 for the scheduler. Lower for the app as a whole.**

I'm confident about the logic layer because the tests have already earned it — writing them found two real bugs (the midnight sort order and parse_time accepting "08:70").

The missing star is that **none of my tests touch app.py**. that's exactly where the worst bug lived, and all 43 tests passed straight through it. so what I can honestly say is that my scheduler is sound, not that my app is.

What I'd test next, in order:

1. **the Streamlit layer**, using Streamlit's own AppTest so the tests go through real widgets and reruns instead of calling methods directly. that's the one gap that has already bitten me.
2. **completing the same task twice in a row** — does it queue two copies?
3. **a conflict between a planned task and a skipped one** — the skipped task has no slot, so I'm not sure what detect_conflicts does with it.
4. **a preferred time earlier than start_time**, like a 06:00 task on a day starting at 08:00.
5. **very long days** — a plan long enough to wrap past midnight twice, which my sort handles but has never been pushed that far.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The part I'm happiest with is that **the plan explains itself.** every task carries the reason it ended up where it did — "at its preferred time", "flexible, fills the gap before 08:45", "needs 90 min, only 15 min left" — so the schedule isn't just a list of times, it's an answer to "why this?".

That came out of a design decision I almost got wrong. I originally had a separate reasons list on the Scheduler sitting next to the planned and skipped lists, and nothing connected a reason to the task it was about. moving the reason onto the Task itself meant the two could never drift apart, and it's what lets both the terminal demo and the Streamlit app show the reasoning without doing any extra work.

I'm also happy with the gap filling. the first version placed tasks in priority order and let the clock only move forward, so one high priority task at 09:00 could drag the whole morning and leave the 08:00 hour empty. placing timed tasks in clock order and letting flexible ones fill the gaps between them is a much better answer and it wasn't much harder to write.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**Test the UI layer.** this is top of the list for the reason above — it's a known blind spot that has already caused a real bug.

**Make the data survive.** everything lives in st.session_state, so a browser refresh wipes every pet and task. saving to a JSON file would make it an app someone could actually use day to day rather than a demo.

**Help with conflicts instead of only reporting them.** right now whoever asked for the earlier time keeps it, even if it's low priority, and the owner has to fix clashes by hand. I'd at least offer a suggestion — "move fetch to 09:30 and the meds fit at 08:30" — while still letting the owner decide.

**Reconsider where the scheduler's output lives.** I'd keep four classes if I did it again, but I'd look harder at whether a small ScheduledItem is worth a fifth. having Task hold both the owner's input and the scheduler's output is the one part of the design I still feel slightly uneasy about.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

**Designing is mostly deciding what you're willing to pay for.**

Almost none of the decisions in this project had an obviously right answer. four classes or five, times as strings or as minutes, priority deciding the order or the clock deciding it — each one was a tradeoff, and picking one meant accepting a specific cost. the useful skill wasn't finding the perfect design, it was being able to name what each choice would cost me and then testing that exact spot.

The AI version of the same lesson: it was genuinely excellent at generating options and finding problems, and completely uninterested in which option I should pick. it suggested a fifth class with a good argument behind it. I said no for reasons that were mine. being the architect meant owning those calls, knowing where they made the system weak, and proving with tests that the weak part still held.
