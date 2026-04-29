"""Data structures representing a set of translations for one key.

A `LocaleEntry` is strictly either:
  * a singular translation (`singular: str`), or
  * a plural translation (`plurals: dict[quantity -> str]`).

A `Translations` collection holds one entry per language and enforces a
uniform mode across all entries (all singular OR all plural).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LocaleEntry:
    singular: Optional[str] = None
    plurals: Optional[Dict[str, str]] = None

    def __post_init__(self):
        has_singular = self.singular is not None
        has_plurals = self.plurals is not None and len(self.plurals) > 0
        if has_singular == has_plurals:
            raise ValueError(
                "LocaleEntry must be either singular or plural, not both/neither."
            )

    def is_plural(self) -> bool:
        return self.plurals is not None


@dataclass
class Translations:
    """Per-language translations of a single base key.

    All entries must share the same mode (singular or plural). The invariant
    is enforced at construction time.
    """

    entries: Dict[str, LocaleEntry] = field(default_factory=dict)

    def __post_init__(self):
        if not self.entries:
            return
        modes = {entry.is_plural() for entry in self.entries.values()}
        if len(modes) > 1:
            raise ValueError(
                "Translations contains a mix of singular and plural entries; "
                "all entries must share the same mode."
            )

    def is_plural(self) -> bool:
        if not self.entries:
            return False
        return next(iter(self.entries.values())).is_plural()

    def languages(self) -> List[str]:
        return list(self.entries.keys())

    def missing_languages(self, active_languages: List[str]) -> List[str]:
        return [lang for lang in active_languages if lang not in self.entries]
