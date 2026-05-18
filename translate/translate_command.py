"""Top-level orchestration for the `ink translate` command."""

from typing import Dict, List, Union

from common_utils import select_in_list, cancel_ink_command
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


def prompt_for_confirmation(string_key: str, full: Translations, string_tags: List[str]) -> bool:
    print()
    for lang, entry in full.entries.items():
        print(f"{lang}: {format_locale_entry(entry)}")
    print()
    print(f"id: {string_key}")
    print(f"tags: {string_tags}")
    print()
    return (input("Are the following translations correct? [Y/n]: ").lower() or "y") == "y"


def format_locale_entry(entry: LocaleEntry) -> str:
    if entry.is_plural():
        return "\n" + "\n".join([f"    {form}: {plural}" for form, plural in entry.plurals])
    else:
        return entry.singular


def run(args) -> None:
    seeds: Dict[str, SeedValue] = getattr(args, "seeds", None) or {}
    string_key: str = args.key
    string_tags: List[str] = list(args.tags or [])

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

    if string_key is None:
        string_key = input("Input the string ID to use (ex: sentFilesTitle): ")

    if len(string_tags) == 0:
        choices = ["android, ios", "android", "custom tags…"]
        tag_choice = select_in_list("Select tags for this string", choices)
        if tag_choice == "custom tags…":
            tag_choice = input("Input the coma separated tags (ex: android, ios, my kSuite): ")

        string_tags = [el.strip() for el in tag_choice.split(",")]

    seeds_translations = _seeds_to_translations(seeds)
    missing = seeds_translations.missing_languages(languages)

    if missing:
        prompt = construct_prompt(seeds, languages)
        spinner = Spinner("Generating translations…")
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

    is_valid = prompt_for_confirmation(string_key, full, string_tags)
    if not is_valid:
        cancel_ink_command()

    upload_translations(string_key, full, string_tags)
