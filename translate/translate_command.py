"""Top-level orchestration for the `ink translate` command."""

from typing import Dict, List, Union

import config
from translate.ai_client import generate_translations
from translate.extractor import parse_response
from translate.languages import get_languages_for_project
from translate.prompt_builder import construct_prompt, is_plural_mode
from translate.spinner import Spinner
from translate.translation import LocaleEntry, Translations
from translate.uploader import upload_translations
from translate.validation import (
    TranslationConsistencyError,
    verify_seed_consistency,
)

SeedValue = Union[str, Dict[str, str]]


def _seeds_to_translations(seeds: Dict[str, SeedValue]) -> Translations:
    entries = {}
    for lang, value in seeds.items():
        if isinstance(value, str):
            entries[lang] = LocaleEntry(singular=value)
        else:
            entries[lang] = LocaleEntry(plurals=dict(value))
    return Translations(entries=entries)


def _merge_translations(seeds: Translations, generated: Translations) -> Translations:
    merged = dict(seeds.entries)
    for lang, entry in generated.entries.items():
        merged.setdefault(lang, entry)
    return Translations(entries=merged)


def prompt_for_confirmation(full: Translations):
    for lang, entry in full.entries.items():
        print(f"{lang}: {format_locale_entry(entry)}")
    print()
    return input("Are the following translations correct? [Y/n]: ").lower() or "y" == "y"


def format_locale_entry(entry: LocaleEntry) -> str:
    if entry.is_plural():
        return "\n" + "\n".join([f"    {form}: {plural}" for form, plural in entry.plurals])
    else:
        return entry.singular


def run(args) -> None:
    seeds: Dict[str, SeedValue] = getattr(args, "seeds", None) or {}
    base_key: str = args.key
    extra_tags: List[str] = list(args.tags or [])

    languages = get_languages_for_project()

    try:
        verify_seed_consistency(seeds)
    except TranslationConsistencyError as exc:
        print(f"Invalid seed translations:\n{exc}")
        raise SystemExit(1)

    unknown = [lang for lang in seeds.keys() if lang not in languages]
    if unknown:
        print(
            "Some seed languages are not part of this project's language list "
            f"({', '.join(languages)}): {', '.join(sorted(unknown))}"
        )
        raise SystemExit(1)

    seeds_translations = _seeds_to_translations(seeds)
    missing = seeds_translations.missing_languages(languages)

    if missing:
        prompt = construct_prompt(seeds, languages)
        spinner = Spinner("Generating translations...")
        spinner.start()
        response_text = generate_translations(prompt)
        spinner.stop()
        generated_translations = parse_response(response_text, languages)

        # Re-verify the AI output using the same rules so a bad model response
        # fails fast with a clear error.
        generated_seeds: Dict[str, SeedValue] = {}
        for lang, entry in generated_translations.entries.items():
            if entry.is_plural():
                generated_seeds[lang] = dict(entry.plurals)
            else:
                generated_seeds[lang] = entry.singular

        if generated_seeds:
            try:
                verify_seed_consistency(generated_seeds)
            except TranslationConsistencyError as exc:
                print(f"AI response failed validation:\n{exc}")
                raise SystemExit(1)

        # Make sure the AI mode matches the seed mode (uniform mode invariant).
        seed_is_plural = is_plural_mode(seeds)
        if generated_seeds and is_plural_mode(generated_seeds) != seed_is_plural:
            print(
                "AI response mode (singular/plural) does not match the seed mode."
            )
            raise SystemExit(1)

        full = _merge_translations(seeds_translations, generated_translations)
    else:
        full = seeds_translations

    still_missing = full.missing_languages(languages)
    if still_missing:
        print(
            "Translations are missing for the following languages after AI "
            f"generation: {', '.join(still_missing)}"
        )
        raise SystemExit(1)

    is_valid = prompt_for_confirmation(full)
    if not is_valid:
        raise SystemExit(1)

    project_tag = config.get_project("loco", "tag", raise_error=False)
    tags = list(dict.fromkeys(filter(None, [project_tag] + extra_tags)))

    upload_translations(base_key, full, tags)
