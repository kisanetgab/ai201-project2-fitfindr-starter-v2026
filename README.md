# FitFindr

How to run: see [RUNNING.md](RUNNING.md).

---

## What This Does

A user types what they want in plain language, like "vintage graphic tee under $30". FitFindr searches a file of 40 thrift listings, picks the best match, suggests outfits pairing it with the user's wardrobe (or general styling advice if the wardrobe is empty), and writes a short social-media caption for the find. If nothing matches, it stops and tells the user what to change instead of continuing.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches the listings file for items matching a description, an optional size, and an optional price ceiling.
- **Inputs:** `description` (str), `size` (str, optional), `max_price` (float, optional, in whole US dollars, inclusive)
- **Returns:** A list of up to 10 listing dicts, best keyword match first, each with id, title, description, category, style_tags, size, condition, price, colors, brand (str or None), platform.
- **When it has nothing:** An empty list `[]` (never None).
- **Size matching:** every token of the requested size must appear as a whole token in the listing's size, so "M" matches "S/M" and "M/L" but not "XL".
- **Match rule:** In Unit 3 any one query word matching scored a result. Since the Unit 4 improvement, every query word must appear in the listing's title, description, category, style tags, colors or brand.

### `suggest_outfit`

- **What it does:** Takes one listing and the user's wardrobe and suggests one or two outfits pairing them.
- **Inputs:** `new_item` (dict, one listing), `wardrobe` (dict with an `items` list)
- **Returns:** A string of outfit ideas that name specific wardrobe items.
- **When it has nothing:** If the wardrobe is empty, returns a string of general styling advice for the item instead of failing. If the model can't be reached, `generate()` raises `ModelUnavailable`, which `run_agent` catches.

### `create_fit_card`

- **What it does:** Writes a short social-media-style caption for the item and outfit.
- **Inputs:** `outfit` (str, from suggest_outfit), `new_item` (dict, one listing)
- **Returns:** A caption string of two to four sentences that mentions the item, price and platform.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a descriptive message string instead of raising. If the model can't be reached, `generate()` raises `ModelUnavailable`, which `run_agent` catches.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what to change (price, size, or description) and stop with `session["fit_card"]` still None. Otherwise, store the first result in `session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex. One pattern pulls the price ceiling from phrases like "under $30" or "below 30", and another pulls the size from phrases like "size M" or "in size 8". Whatever text is left becomes the `description`. If no price or size is found, those inputs are passed as None.

**What moves through the session:** `query` (raw text), then `parsed` (dict with description, size, max_price), then `search_results` (list from `search_listings`, called through MCP), then `selected_item` (the first result), then `outfit_input_id` (the item id handed to `suggest_outfit`), then `outfit_suggestion` (string from `suggest_outfit`), then `fit_card` (string from `create_fit_card`). `wardrobe` is set at the start and read by `suggest_outfit`. `error` holds the message if the run ended early, and `fit_card` stays None in that case.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

Outfit:   **Outfit 1: Casual Y2K Streetwear**
Pair the butterfly baby tee with the **baggy straight-leg jeans**, **chunky white sneakers**, and the **black cropped zip hoodie** worn open.

**Outfit 2: Contrast Mix**
Pair the baby tee with the **wide-leg khaki trousers**, **brown leather belt**, and **black combat boots** for a grunge-meets-sweet look.

Fit card: Scored this literal holy grail butterfly baby tee on depop for only $18 and I am never taking it off. Thinking baggy straight-leg jeans and chunky white sneakers for the ultimate casual Y2K streetwear vibe, but it'll also look so good with combat boots for something a little more grunge.
```

```
$ python app.py ask 'designer ballgown size XXS under $5'
No listings matched 'designer ballgown'. Try to raise the price limit above $5, or drop the size (XXS), or use fewer or broader description words.
```

Session state check:

```
$ python -c "from agent import run_agent; from utils.data_loader import get_example_wardrobe; s = run_agent('vintage graphic tee under \$30', get_example_wardrobe()); print(s['parsed']); print(s['selected_item']['id'], s['selected_item']['title'])"
{'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
lst_002 Y2K Baby Tee — Butterfly Print
```

**The three tools, tested one at a time** (Unit 3, before the Unit 4 search change)

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'size': 'S/M', 'price': 18.0, 'platform': 'depop', ...}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'size': 'L', 'price': 24.0, 'platform': 'depop', ...}, ...]
```

```
$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Streetwear**
Pair the vintage Levi's with the **white ribbed tank top**, layered under the **oversized grey crewneck sweatshirt**, and finish with the **chunky white sneakers**.

**Outfit 2: Edge & Denim**
Tuck the **white ribbed tank top** into the Levi's, add the **brown leather belt**, and layer the **vintage black denim jacket** on top with the **black combat boots**.
```

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501s on Depop for just $38 and I am never taking them off. They have that 90s slouchy, broken-in feel that takes years to get naturally. Just gonna live in these and my beat-up white sneakers all autumn.
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* A Tool Inventory draft for the three tools.
- *What came back:* It said `create_fit_card` returns an error string when the model fails.
- *What I changed:* After reading `generate.py`, which raises `ModelUnavailable`, I rewrote that line of the spec.

**Moment 2**

- *What I asked for:* An implementation of `search_listings`.
- *What came back:* It worked, but any single shared word scored, so a sweatshirt whose description says "No graphics" showed up for "graphic tee".
- *What I changed:* I left it in Unit 3 and noted it. In Unit 4 I fixed it by requiring every query word to match.

**Moment 3 (Unit 4)**

- *What I asked for:* The MCP wiring and trace calls for `run_agent`.
- *What came back:* A trace note comparing `item["id"]` to `session["selected_item"]["id"]`, but `item` is `selected_item`, so the comparison cannot fail.
- *What I changed:* I kept it as evidence, but said in my diagnosis that criterion 3 was too easy to pass.

---

## Run Log — Before

Run with `python run_eval.py --label before` (cache off, 5 tries per scenario). Results file: `results/run_2026-10-11_2209_before.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected_item id matches id passed on | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card shape (original wording: 3 sentences or fewer, names item, no "None") | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe still gets outfit and card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Real output from one try (produced by `agent.py::run_agent`, run via `run_eval.py`), criterion 1, try 1:

```
[1] search_listings (via MCP)
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[2] suggest_outfit
      →    received item lst_002 (selected_item is lst_002)
[3] create_fit_card
      out: Scored this little butterfly print Y2K baby tee on Depop for just $18 and I'm so obsessed. It's giving total early 2000s mall rat energy, especially paired with baggy straight-leg jeans, chunky white sneakers, and an open black cropped zip hoodie.
```

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes | 4 of 5 | MET | 5 of 5 tries returned a fit card. |
| 2 | Impossible query stops early | 5 of 5 | MET | 5 of 5 stopped at the branch; the trace had 2 steps and the message named price, size and description. |
| 3 | Selected id matches id passed on | 5 of 5 | MET | The trace showed lst_004 = lst_004 in all 5 tries. |
| 4 | Fit card shape | 4 of 5 | MET | I counted sentences in all 5 cards (2-3 each); each named the item and none contained "None". I scored the original wording. |
| 5 | Empty wardrobe | 4 of 5 | MET | 5 of 5 returned general advice, a fit card and no error. |

**Diagnoses**

I missed nothing, so I checked whether my targets were too easy:

- Criterion 3 could not fail. The trace compares `item["id"]` with `session["selected_item"]["id"]`, and `item` is `selected_item`. I would tighten it by recording the id inside `suggest_outfit`.
- Criterion 4 checks form only, not accuracy. One card said "So ready for spring" in October. I would require price and platform to appear.
- Criterion 1's 4-of-5 target was loose: parsing and MCP never failed in 5 tries.
- The real weakness was the search tool (a tool-step problem): any single shared word scored, so "90s track jacket in size M" returned a silk slip dress and a leather bomber, and "denim jacket under $50" returned Levi's jeans. No criterion measured it. That is the step I improved.

---

## Loop Trace

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[2] suggest_outfit
      in:  dict with keys: item_id, wardrobe_items
      out: **Outfit 1: Casual Y2K Streetwear** Pair the butterfly baby tee with the **baggy straight-leg jeans**, **chunk…
      →    received item lst_002 (selected_item is lst_002)
[3] create_fit_card
      in:  dict with keys: item_id
      out: Scored this literal holy grail butterfly baby tee on depop for only $18 and I am never taking it off. Thinking…
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[2] branch
      →    empty search, stopping before suggest_outfit
```

**Failure modes triggered on purpose**

- Empty search: "No listings matched 'designer ballgown'. Try to raise the price limit above $5, or drop the size (XXS), or use fewer or broader description words."
- Empty wardrobe (`--empty-wardrobe`, 'denim jacket under $50'): returned general styling advice and a fit card, no error.
- Model unavailable (one character of the key changed, 'platform sneakers size 8'): "The model couldn't be reached, so no outfit or fit card was made. Check GEMINI_API_KEY in your .env file, or wait a minute if you've been running many queries, then try again."

**On the MCP move:** I registered `search_listings` in `mcp_server.py` and replaced the direct call in `run_agent` with `mcp_client.call_tool`. The same list of listing dicts came back. The only problem was running outside `.venv`, which gave "No module named 'mcp'"; activating `.venv` fixed it.

---

## The Improvement

**What I changed:** In `tools.py::search_listings`, the match rule went from "any one query word appears" (`score > 0`) to "every query word appears" (`query <= haystack`).

**Which failure it was meant to fix:** Loose search results at the tool step (a slip dress and a bomber for a track jacket query, Levi's jeans for a denim jacket query).

Result counts, before to after: graphic tee query 10 to 3, track jacket 4 to 1, denim jacket 7 to 1, ballgown 0 to 0. The top result was identical in every scenario.

### Run Log — After

Run with `python run_eval.py --label after`. Results file: `results/run_2026-10-11_2220_after.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Selected id matches | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card shape | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes for result quality: the irrelevant items disappeared (counts above). All five criteria were still MET after the change (criterion 4 scored on the original wording: 2-3 sentences each, item named, no "None"), so the improvement raised search precision without breaking the loop. The criteria did not change because they measure loop completion and state, not search quality. Tradeoff: stricter matching can return nothing for phrasing like "t-shirt" vs "tee".

---

## What's Still Broken

- Search is brittle on phrasing: there are no synonyms (tee/t-shirt), so a reasonable query can return nothing. Next I would fall back to any-word matching when all-words returns nothing, and say so.
- Criterion 3 can't fail as written (the same object is compared to itself). I would record the id inside `suggest_outfit`.
- Criterion 4 checks form, not accuracy, price or platform.
- The agent always picks the first result and never asks.
- I stopped at one improvement, which was the scope, and the deadline was tonight.
