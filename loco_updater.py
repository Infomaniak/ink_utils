import os
import shutil
import subprocess
import requests
import zipfile
import xml.etree.ElementTree as ET

import config as config
from loco_validation_rules import ExistenceRule, FrenchEmailRule

cwd = "/tmp/ink_archive"
archive_name = "downloaded.zip"
value_folders = ['values', 'values-de', 'values-es', 'values-fr', 'values-it']

project_root = config.get('loco', 'project_root')
project_path = project_root + "/src/main/res"

forbidden_sequences = ["'", "..."]
forbidden_rules = [ExistenceRule(sequence) for sequence in forbidden_sequences]
rules = [*forbidden_rules]

language_rules = {
    "en": [ExistenceRule("e-mail")],
    "fr": [FrenchEmailRule()],
    "de": [
        ExistenceRule("ẞ"),
        ExistenceRule("gespräch"),
    ],
    "it": [],
    "es": []
}


def update_loco():
    loco_key = config.get('loco', 'loco_key')
    zip_url = f"https://localise.biz/api/export/archive/xml.zip?format=android&filter=android&fallback=en&order=id&key={loco_key}"

    archive_path = download_zip(zip_url)
    if archive_path is None:
        return

    print("String resources downloaded successfully")

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(cwd)

    os.chdir(cwd)
    files = os.listdir('.')

    os.chdir(project_root)

    # Copy the strings.xml files from the archive to the project's values folder
    for value_folder in value_folders:
        target_file = f'{project_path}/{value_folder}/strings.xml'
        source_file = f'{cwd}/{files[0]}/res/{value_folder}/strings.xml'

        shutil.copy(source_file, target_file)

        fix_loco_header(target_file)

    print("String resources updated")

    shutil.rmtree(cwd)
    print("Deleting temporary downloaded strings resources")


def download_zip(zip_url):
    archive_path = cwd + "/" + archive_name

    response = requests.get(zip_url)

    if response.status_code != 200:
        print("Error: When trying to download translations received response.status_code =", response.status_code)
        return None

    os.makedirs(cwd, exist_ok=True)

    with open(archive_path, "wb+") as f:
        f.write(response.content)

    return archive_path


def fix_loco_header(target_file):
    result = subprocess.run(f"git diff {target_file}", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    diff = result.stdout
    removed_lines = []
    added_lines = []
    for line in diff.split("\n")[5:]:
        if line[0] == "-":
            removed_lines.append(line[1:])
        elif line[0] == "+":
            added_lines.append(line[1:])
        else:
            break
    to_replace = "\n".join(added_lines)
    replace_with = "\n".join(removed_lines)
    with open(target_file, "r+") as fd:
        file_content = fd.read()
        fixed_file = file_content.replace(to_replace, replace_with)
        fd.seek(0)
        fd.write(fixed_file)


def validate_strings():
    error_count = 0

    for value_folder in value_folders:
        current_file = f'{project_path}/{value_folder}/strings.xml'
        tree = ET.parse(current_file)

        parts = value_folder.split("-")
        language = "en" if len(parts) < 2 else parts[-1]

        for element in tree.getroot():
            tag = element.tag
            name = element.get("name")
            value = element.text

            if tag == "string":
                error_count += validate_string(language, name, value)
            elif tag == "plurals":
                error_count += validate_plural(element, language, name)

    return error_count


def validate_string(language, name, value):
    error_count = 0

    for rule in rules:
        if rule.check(value, language, name):
            error_count += 1

    for language_rule in language_rules[language]:
        if language_rule.check(value, language, name):
            error_count += 1

    return error_count


def validate_plural(plural, language, name):
    error_count = 0

    for element in plural:
        plural_name = f"{name}-{element.get('quantity')}"
        plural_value = element.text

        error_count += validate_string(language, plural_name, plural_value)

    return error_count
