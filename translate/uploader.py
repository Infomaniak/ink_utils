"""Upload translations to the backend.

The backend API only accepts a single key per call, so this module exposes:

  * `upload_key`            — the primitive that uploads exactly one key.
  * `upload_translations`   — the orchestrator that, given a base key and a
                              `Translations` object, derives the concrete keys
                              (one per quantity in plural mode, just the base
                              key in singular mode) and calls `upload_key` for
                              each of them.

The actual HTTP call inside `upload_key` is left as a stub; the orchestration
logic above doesn't need to know how the request is shaped.
"""

from typing import Dict, List

from translate.languages import allowed_quantities
from translate.translation import Translations


def upload_key(key: str, translations_per_language: Dict[str, str], tags: List[str]) -> None:
    """Upload exactly one key with one value per language.

    `translations_per_language` maps language code -> translated value.
    `tags` is the list of tags to attach on the backend.
    """
    # TODO: replace with the real backend HTTP call once the endpoint shape is
    # finalized. Kept as a stub so the orchestration layer can be exercised.
    print(f"[upload] key={key} tags={tags}")
    for lang, value in translations_per_language.items():
        print(f"  {lang}: {value}")


def upload_translations(base_key: str, translations: Translations, tags: List[str]) -> None:
    """Orchestrate the upload of a `Translations` object as one or more keys.

    In singular mode this calls `upload_key` once with `base_key`.
    In plural mode this derives `<base_key>-<quantity>` for every quantity
    defined for at least one language in `translations` and calls `upload_key`
    once per derived key, passing the per-language value for that quantity.
    """
    if not translations.entries:
        raise ValueError("No translations to upload.")

    if not translations.is_plural():
        per_language = {lang: entry.singular for lang, entry in translations.entries.items()}
        upload_key(base_key, per_language, tags)
        return

    # Plural mode: collect the union of quantities present across languages.
    # `verify_seed_consistency` ensures each language carries exactly its
    # allowed set, so the union is well defined.
    quantities_in_order: List[str] = []
    seen = set()
    for lang in translations.entries:
        for quantity in allowed_quantities(lang):
            if quantity not in seen:
                seen.add(quantity)
                quantities_in_order.append(quantity)

    for quantity in quantities_in_order:
        per_language = {}
        for lang, entry in translations.entries.items():
            if entry.plurals and quantity in entry.plurals:
                per_language[lang] = entry.plurals[quantity]
        if not per_language:
            continue
        derived_key = f"{base_key}-{quantity}"
        upload_key(derived_key, per_language, tags)
