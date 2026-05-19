"""Upload translations to the backend.

The backend API only accepts a single key per call, so this module exposes:

  * `upload_key`            — the primitive that uploads exactly one key.
  * `upload_translations`   — the orchestrator that, given a base key and a
                              `Translations` object, derives the concrete keys
                              (one per quantity in plural mode, just the base
                              key in singular mode) and calls `upload_key` for
                              each of them.

"""
import xml.etree.ElementTree as ET
from typing import Dict, List

import requests

import config
from translate.translation import Translations

_LOCO_IMPORT_URL = "https://localise.biz/api/import/json"
_LOCO_ASSETS_URL = "https://localise.biz/api/assets"


def is_key_already_present(key: str) -> bool:
    """
    Returns True if the localisation key exists in on the remote, otherwise returns False.
    """

    url = f"{_LOCO_ASSETS_URL}/{key}"
    headers = {
        "Authorization": f"Loco {config.get_project('loco', 'loco_key')}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return True

        if response.status_code == 404:
            return False

        # Raise unexpected API errors
        response.raise_for_status()

    except requests.RequestException as exception:
        raise RuntimeError(f"Failed to check key existence: {exception}") from exception

    return False


def upload_key(key: str, translations_per_language: Dict[str, str], tags: List[str]) -> None:
    """Upload exactly one key with one value per language.

    `translations_per_language` maps language code -> translated value.
    `tags` is the list of tags to attach on the backend.
    """
    api_key = config.get_project("loco", "loco_key")
    tags_param = ",".join(tags) if tags else None

    for lang, value in translations_per_language.items():
        params = {
            "key": api_key,
            "locale": lang,
        }
        if tags_param:
            params["tag-new"] = tags_param
            params["tag-existing"] = tags_param

        response = requests.post(
            _LOCO_IMPORT_URL,
            params=params,
            json={key: value},
        )

        if not response.ok:
            if response.status_code == 403:
                print("Your loco api key doesn't have write permissions")
                raise SystemExit(1)
            else:
                raise RuntimeError(
                    f"Failed to upload key '{key}' for locale '{lang}': "
                    f"{response.status_code} {response.reason}"
                )


def upload_translations(base_key: str, translations: Translations, tags: List[str]) -> None:
    """Orchestrate the upload of a `Translations` object as one or more keys.

    In singular mode this calls `upload_key` once with `base_key`.
    In plural mode this derives `<base_key>-<quantity>` for every quantity
    defined for at least one language in `translations` and calls `upload_key`
    once per derived key, passing the per-language value for that quantity.
    """
    if not translations.entries:
        raise ValueError("No translations to upload.")

    if translations.is_plural():
        _upload_plural_key(base_key, tags, translations)
    else:
        _upload_plain_key(base_key, tags, translations)


def _build_android_xml(base_key: str, plurals: Dict[str, str]) -> bytes:
    """
    Build Android strings XML in memory with plurals.
    Produces a valid <resources> document containing a single <plurals> element
    with one <item> per quantity form.

    `plurals` maps quantity (e.g. "one", "other", "few") to the translated string.
    """

    resources = ET.Element("resources")
    plurals_elem = ET.SubElement(resources, "plurals")
    plurals_elem.set("name", base_key)

    for quantity, value in plurals.items():
        item = ET.SubElement(plurals_elem, "item")
        item.set("quantity", quantity)
        item.text = value

    return ET.tostring(resources, encoding="UTF-8", xml_declaration=True)


def _upload_plural_key(base_key: str, tags: list[str], translations: Translations):
    """Upload a plural key by importing one Android XML per locale.

    Each locale may have a different set of quantity forms (e.g. "one"/"other"
    for English, "one"/"few"/"many"/"other" for Polish). We build and upload a
    complete XML per locale so all plural forms are sent together.
    """
    tags_param = ",".join(tags) if tags else None

    for lang, entry in translations.entries.items():
        if not entry.plurals:
            continue

        xml_bytes = _build_android_xml(base_key, entry.plurals)

        params = {
            "locale": lang,
            "index": "id",
        }
        if tags_param:
            params["tag-new"] = tags_param
            params["tag-existing"] = tags_param

        response = requests.post(
            "https://localise.biz/api/import/xml",
            params=params,
            headers={
                "Authorization": f"Loco {config.get_project('loco', 'loco_key')}",
                "Content-Type": "application/xml",
            },
            data=xml_bytes,
        )

        if not response.ok:
            if response.status_code == 403:
                print("Your loco api key doesn't have write permissions")
                raise SystemExit(1)
            raise RuntimeError(
                f"Failed to import plural key '{base_key}' for locale '{lang}': "
                f"{response.status_code} {response.text}"
            )


def _upload_plain_key(base_key: str, tags: list[str], translations: Translations):
    per_language = {lang: entry.singular for lang, entry in translations.entries.items()}
    upload_key(base_key, per_language, tags)
