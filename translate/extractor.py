"""Parse the raw AI text response into a structured `Translations` object.

The expected line format is `<code>: <value>` for singular and
`<code>-<quantity>: <value>` for plural. For robustness, lines using
`<code>.<quantity>: <value>` are also accepted as a fallback when a model
emits the dotted form.
"""

import re
from typing import Dict, List

from translate.languages import allowed_quantities
from translate.translation import LocaleEntry, Translations

# `code` and `quantity` are matched loosely so that this stays readable; the
# downstream consistency check is what enforces correctness against the
# active language list and quantity rules.
_LINE_PATTERN = re.compile(
    r"""^\s*
        (?P<code>[A-Za-z]{2,3})                       # language code (no region)
        (?:[-.](?P<quantity>one|other|few|many))?     # plural quantity (matches PLURAL_QUANTITIES)
        \s*[:=]\s*
        (?P<value>.+?)
        \s*$""",
    re.VERBOSE,
)


def parse_response(response_text: str, languages: List[str]) -> Translations:
    """Parse the AI response into a `Translations` object.

    Only lines whose language code is in `languages` are kept. Trailing or
    leading blank lines, code fences and stray prose are silently skipped.
    """
    accepted_codes = set(languages)
    singular_entries: Dict[str, str] = {}
    plural_entries: Dict[str, Dict[str, str]] = {}

    for raw_line in response_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("```") or line.startswith("#"):
            continue

        match = _LINE_PATTERN.match(line)
        if match is None:
            continue

        code = match.group("code")
        if code not in accepted_codes:
            continue

        quantity = match.group("quantity")
        value = match.group("value").strip()
        # Strip surrounding quotes a model might have added.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        if quantity is None:
            singular_entries[code] = value
        else:
            plural_entries.setdefault(code, {})[quantity] = value

    entries = {}
    for code, value in singular_entries.items():
        entries[code] = LocaleEntry(singular=value)
    for code, plurals in plural_entries.items():
        # Keep only the quantities allowed for the language; ignore extras.
        allowed = set(allowed_quantities(code))
        filtered = {q: v for q, v in plurals.items() if q in allowed}
        if filtered:
            entries[code] = LocaleEntry(plurals=filtered)

    return Translations(entries=entries)
