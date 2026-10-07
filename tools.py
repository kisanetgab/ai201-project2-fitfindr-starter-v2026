"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""
import re
import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings

_STOPWORDS = {
    "a", "an", "the", "in", "for", "of", "and", "or", "with", "to", "i",
    "im", "me", "my", "want", "looking", "find", "need", "size", "under",
    "below", "over", "max", "up", "something",
}


def _tokens(text: str) -> set[str]:
    """Lowercase words, with a crude plural strip so 'tees' matches 'tee'."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words}


def _size_matches(want: str, listing_size: str) -> bool:
    """Whole-token match: 'M' matches 'S/M' but not 'XL' or 'US 9'."""
    want_tokens = set(re.findall(r"[a-z0-9]+", want.lower()))
    have_tokens = set(re.findall(r"[a-z0-9]+", listing_size.lower()))
    return bool(want_tokens) and want_tokens <= have_tokens




# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Return listings matching the description, size and price ceiling, best
    match first (at most config.SEARCH_RESULT_LIMIT). Returns [] when nothing
    matches, never None.
    """
    query = _tokens(description or "") - _STOPWORDS
    scored = []
    for item in load_listings():
        if max_price is not None and item["price"] > max_price:
            continue
        if size and not _size_matches(size, item["size"]):
            continue
        haystack = _tokens(" ".join([
            item["title"],
            item["description"],
            item["category"],
            " ".join(item["style_tags"]),
            " ".join(item["colors"]),
            item["brand"] or "",
        ]))
        score = len(query & haystack)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored][: config.SEARCH_RESULT_LIMIT]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _describe(item: dict) -> str:
    brand = f" by {item['brand']}" if item.get("brand") else ""
    return (
        f"{item['title']}{brand} ({', '.join(item['colors'])}; "
        f"style: {', '.join(item['style_tags'])}; ${item['price']:.0f} on {item['platform']})"
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Suggest one or two outfits pairing new_item with the wardrobe. With an
    empty wardrobe, returns general styling advice instead.
    """
    items = (wardrobe or {}).get("items", [])
    if not items:
        prompt = (
            f"Someone just found this thrifted piece: {_describe(new_item)}. "
            "They have no wardrobe saved. Suggest one or two outfits built "
            "around it, using common basics they likely own. Keep it short."
        )
    else:
        owned = "\n".join(
            f"- {w['name']} ({', '.join(w['colors'])}; {w.get('notes', '')})"
            for w in items
        )
        prompt = (
            f"Someone just found this thrifted piece: {_describe(new_item)}.\n"
            f"Their wardrobe:\n{owned}\n\n"
            "Suggest one or two outfits that pair the new piece with specific "
            "items from the wardrobe, naming those items. Keep it short."
        )
    return generate(prompt)



# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a two-to-four sentence caption for the find. If outfit is empty,
    returns a descriptive message instead of raising.
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card yet: there's no outfit suggestion to base it on."
    prompt = (
        "Write a two-to-four sentence social media caption for a thrift find. "
        "It should sound like a real person's post, not a product listing. "
        f"Item: {new_item['title']}, ${new_item['price']:.0f} on {new_item['platform']}. "
        "Mention the item, price, and platform once each, and be specific about "
        "the vibe. Do not mention a brand unless one is given here: "
        f"{new_item.get('brand') or 'none'}.\n"
        f"Outfit idea: {outfit}"
    )
    return generate(prompt)
