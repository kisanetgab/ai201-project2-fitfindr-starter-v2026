"""
The FitFindr planning loop.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# -- session state -------------------------------------------------------------

def new_session(query: str, wardrobe: dict) -> dict:
    """A fresh session for one user interaction."""
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# -- query parsing (regex) -----------------------------------------------------

def _parse_query(query: str) -> dict:
    """Regex parse: price ceiling, size, and whatever text is left."""
    text = query
    max_price = None
    size = None

    m = re.search(
        r"(?:under|below|less than|max|up to)\s*\$?\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?)",
        text, re.I,
    )
    if m:
        max_price = float(m.group(1) or m.group(2))
        text = text.replace(m.group(0), " ")

    m = re.search(r"\b(?:in\s+)?size\s+([a-z0-9/]+)", text, re.I)
    if m:
        size = m.group(1)
        text = text.replace(m.group(0), " ")

    description = re.sub(r"\s+", " ", text).strip(" ,.")
    return {"description": description, "size": size, "max_price": max_price}


# -- planning loop -------------------------------------------------------------

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.
    Check session["error"] first: if it isn't None, the run ended early.
    """
    session = new_session(query, wardrobe)
    count = 0

    count += 1
    trace.check_iterations(count)
    session["parsed"] = _parse_query(query)
    p = session["parsed"]

    count += 1
    trace.check_iterations(count)
    session["search_results"] = search_listings(
        p["description"], size=p["size"], max_price=p["max_price"]
    )

    # THE BRANCH: nothing found -> stop before suggest_outfit
    if not session["search_results"]:
        tips = []
        if p["max_price"] is not None:
            tips.append(f"raise the price limit above ${p['max_price']:.0f}")
        if p["size"]:
            tips.append(f"drop the size ({p['size']})")
        tips.append("use fewer or broader description words")
        session["error"] = (
            f"No listings matched '{p['description']}'. Try to "
            + ", or ".join(tips) + "."
        )
        return session

    session["selected_item"] = session["search_results"][0]

    count += 1
    trace.check_iterations(count)
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], session["wardrobe"]
    )

    count += 1
    trace.check_iterations(count)
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )
    return session


# -- running it directly -------------------------------------------------------

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
