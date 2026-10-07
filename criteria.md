# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
My query parser is a regex, so it only catches the phrasings I planned for, and
the sizes in the data are messy strings like "S/M" and "W30 L30" that a simple
match can miss. Two of the three steps also call the model, which can fail or
rate-limit. So 5 of 5 would be unrealistic. I set 4 of 5 because I expect
occasional misses from phrasing or the model, but more than one miss would mean
a real bug.


---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path has no model call in it. The branch only checks whether
`search_listings` returned an empty list, which is plain code that behaves the
same every time. Criterion 1 depends on regex phrasing and model output, but
this one doesn't, so any miss would be a bug in my branch and not randomness.
That's why I can hold it to 5 of 5.

---

## 3. Something about state

In a matching run, the id of session["selected_item"] is the same id as the item that suggest_outfit received (checked by printing both) in 5 of 5 tries.


**Why this target:**: The handoff goes through session["selected_item"] with no model involved, so the same code runs every time. Any miss would mean a real bug, not randomness, so I set it at 5 of 5.

---

## 4. Something about the fit card

Every fit card is non-empty, is 3 sentences or fewer, names the item (title or type), and contains no "None" or blank brand, in at least 4 of 5 tries.


**Why this target:**
The model varies its wording (TEMPERATURE is 0.9), so I can't demand identical text. I check observable traits instead. 4 of 5 because some listings have a null brand, which can leak into the caption.


---

## 5. Your choice

Given a query that matches a listing and an empty wardrobe, the run ends with session["error"] equal to None, and both session["outfit_suggestion"] and session["fit_card"] are non-empty strings, in at least 4 of 5 tries.



**Why this target:**

suggest_outfit and create_fit_card both call the model, so some variation is expected and I allow one miss in five. The empty-wardrobe path has to return general advice instead of crashing, and that part is code I control


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
