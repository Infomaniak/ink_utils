"""Active language list and plural quantity rules for the `ink translate` command.

The default language list mirrors the locales that the loco updater currently
ships translations for. Individual projects can override it via an optional
`translate.languages` block in `settings.yml`.
"""

import config

# Default 13 languages: English (default values folder) + the 12 locale folders
# enumerated in `loco_updater.value_folders`.
DEFAULT_LANGUAGES = [
    "en",
    "de",
    "es",
    "fr",
    "it",
    "da",
    "el",
    "fi",
    "nb",
    "nl",
    "pl",
    "pt",
    "sv",
]

# Quantity sets per language. Anything not explicitly listed falls back to
# `_default`. CLDR-wise this is the simplified set of plural forms that we
# actually use in the apps.
PLURAL_QUANTITIES = {
    "_default": ["one", "other"],
    "pl": ["one", "few", "many", "other"],
}


def get_languages_for_project():
    """Return the language list configured for the active project.

    Reads the optional `translate.languages` setting from `settings.yml`.
    Falls back to `DEFAULT_LANGUAGES` when not set.
    """
    configured = config.get_project("translate", "languages", raise_error=False)
    if configured is None:
        return list(DEFAULT_LANGUAGES)
    if not isinstance(configured, list) or not all(isinstance(c, str) for c in configured):
        raise ValueError(
            "Invalid `translate.languages` in settings.yml: expected a list of language codes (strings)."
        )
    return list(configured)


def allowed_quantities(language):
    """Return the list of allowed plural quantities for the given language code."""
    return list(PLURAL_QUANTITIES.get(language, PLURAL_QUANTITIES["_default"]))
