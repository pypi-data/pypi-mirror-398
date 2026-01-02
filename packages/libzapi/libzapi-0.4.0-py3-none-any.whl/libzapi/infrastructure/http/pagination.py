from __future__ import annotations
from typing import Iterator


def next_link(data: dict, base_url: str) -> str | None:
    """
    Zendesk style cursor link extractor.
    Accepts absolute or relative next links and returns a relative path.
    """
    links = data.get("links") or {}
    nxt = links.get("next")
    if not nxt:
        return None
    return nxt.replace(base_url, "") if isinstance(nxt, str) and nxt.startswith("https://") else nxt


def yield_pages(get_json, first_path: str, base_url: str) -> Iterator[dict]:
    """
    Generic pager. get_json is a callable like http.get that returns a dict.
    Yields the full page payload dict so callers can choose the list key.
    """
    path = first_path
    while path:
        data = get_json(path)
        yield data
        path = next_link(data, base_url)


def yield_items(get_json, first_path: str, base_url: str, items_key: str) -> Iterator[dict]:
    """
    Convenience iterator that yields individual items from a list key.
    """
    for page in yield_pages(get_json, first_path, base_url):
        for obj in page.get(items_key, []) or []:
            yield obj
