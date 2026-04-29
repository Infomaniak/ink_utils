"""Consistency checks for translation seed input and AI extractor output.

The same set of rules is reused for:
  * the user-supplied seed translations (passed via the CLI), and
  * the parsed translations returned by the AI extractor.

Failing fast with a clear error message is the goal — the rest of the
translate pipeline assumes a clean, uniform input.
"""

from typing import Dict, Union

from translate.languages import allowed_quantities


SeedValue = Union[str, Dict[str, str]]


class TranslationConsistencyError(ValueError):
    """Raised when seed translations or AI output violate the consistency rules."""


def verify_seed_consistency(seeds: Dict[str, SeedValue]) -> None:
    """Verify that the given seeds form a consistent set.

    Rules:
      1. Each entry is either a string (singular) or a dict (plural), never both.
      2. All entries must share the same mode (all singular or all plural).
      3. For plural entries, the supplied quantities must equal the language's
         allowed set exactly (no missing, no extras).
    """
    if not seeds:
        raise TranslationConsistencyError(
            "No translations were provided. At least one seed translation is required."
        )

    singular_langs = []
    plural_langs = []
    invalid_type_langs = []

    for lang, value in seeds.items():
        if isinstance(value, str):
            singular_langs.append(lang)
        elif isinstance(value, dict) and value:
            plural_langs.append(lang)
        else:
            invalid_type_langs.append(lang)

    if invalid_type_langs:
        raise TranslationConsistencyError(
            "These languages have an invalid translation value (expected a string for "
            f"singular or a non-empty quantity->value mapping for plural): "
            f"{', '.join(sorted(invalid_type_langs))}"
        )

    if singular_langs and plural_langs:
        raise TranslationConsistencyError(
            "Mixed singular and plural inputs are not supported. "
            f"Singular: {', '.join(sorted(singular_langs))}. "
            f"Plural: {', '.join(sorted(plural_langs))}. "
            "Provide either only singular values or only plural values."
        )

    if plural_langs:
        errors = []
        for lang in plural_langs:
            expected = set(allowed_quantities(lang))
            provided = set(seeds[lang].keys())
            missing = expected - provided
            extra = provided - expected
            if missing or extra:
                parts = []
                if missing:
                    parts.append(f"missing quantities: {', '.join(sorted(missing))}")
                if extra:
                    parts.append(f"unexpected quantities: {', '.join(sorted(extra))}")
                errors.append(f"  - {lang}: {'; '.join(parts)} (expected exactly: {', '.join(sorted(expected))})")
        if errors:
            raise TranslationConsistencyError(
                "Plural quantities don't match the expected set for these languages:\n"
                + "\n".join(errors)
            )
