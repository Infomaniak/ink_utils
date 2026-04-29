"""Build the prompt sent to the AI client for translation generation."""

from typing import Dict, List, Union

from translate.languages import allowed_quantities

SeedValue = Union[str, Dict[str, str]]


def is_plural_mode(seeds: Dict[str, SeedValue]) -> bool:
    """Return True if the seed input is in plural mode.

    Assumes seeds have already been validated by `verify_seed_consistency`,
    so picking any entry suffices.
    """
    if not seeds:
        return False
    sample = next(iter(seeds.values()))
    return isinstance(sample, dict)


def construct_prompt(seeds: Dict[str, SeedValue], languages: List[str]) -> str:
    """Construct the AI prompt asking for the missing translations.

    The output format the model is asked to follow uses the `<code>-<quantity>`
    style for plurals (e.g. `fr-other`) which mirrors what the loco updater
    uses internally for plural keys.
    """
    plural_mode = is_plural_mode(seeds)
    missing = [lang for lang in languages if lang not in seeds]

    lines = [
        "You are a professional translator working on a mobile application.",
        "Translate the provided source text(s) into the requested target languages.",
        "Preserve placeholders (e.g. %s, %1$d, {n}, %@), punctuation style, and tone.",
        "Do not add explanations, do not wrap the output in code fences, output only the requested lines.",
        "",
        "Provided translations (use these as the source of truth):",
    ]

    if plural_mode:
        for lang, plurals in seeds.items():
            for quantity in allowed_quantities(lang):
                if quantity in plurals:
                    lines.append(f"{lang}-{quantity}: {plurals[quantity]}")
        lines.append("")
        lines.append(f"Generate translations for these languages: {', '.join(missing)}")
        lines.append(
            "Output one line per language and quantity in the format `<code>-<quantity>: <translation>`."
        )
        lines.append(
            "Use quantities `one, other` for all languages except `pl` which uses `one, few, many, other`."
        )
    else:
        for lang, value in seeds.items():
            lines.append(f"{lang}: {value}")
        lines.append("")
        lines.append(f"Generate translations for these languages: {', '.join(missing)}")
        lines.append("Output one line per language in the format `<code>: <translation>`.")

    return "\n".join(lines)
