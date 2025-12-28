"""
Pure Python replacement utilities for dictionary entries.

The functions in this module avoid any partial or fuzzy matching and rely on
exact string replacements sorted from longest to shortest to prevent substring
collisions.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import List, Tuple

from .models import Entry


def pseudonym_for(entry: Entry) -> str:
    """
    Build a deterministic pseudonym based on category and primary key.

    The primary key must be set because IDs provide the stable source of truth.
    """
    if entry.id is None:
        raise ValueError("Entry must be saved before generating a pseudonym.")

    prefix = entry.category.capitalize()
    return f"{prefix}{entry.id}"


def replace(text: str, entries: Iterable[Entry] | None = None) -> str:
    """
    Replace internal identifiers in text using the provided entries.

    Entries are applied from longest value to shortest to avoid substring
    collisions. Only active entries are considered.
    """
    replacements = _sorted_replacements(_load_entries(entries))

    output = text
    for value, pseudonym in replacements:
        output = output.replace(value, pseudonym)

    return output


def _load_entries(entries: Iterable[Entry] | None) -> Iterable[Entry]:
    if entries is None:
        return Entry.objects.filter(is_active=True).iterator()
    return (entry for entry in entries if entry.is_active)


def _sorted_replacements(
    entries: Iterable[Entry],
) -> List[Tuple[str, str]]:
    replacements: List[Tuple[str, str]] = []
    for entry in entries:
        if not entry.value:
            raise ValueError("Entry value cannot be empty.")
        replacements.append((entry.value, pseudonym_for(entry)))

    replacements.sort(key=lambda item: (-len(item[0]), item[0], item[1]))
    return replacements
