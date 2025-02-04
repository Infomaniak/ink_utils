import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from enum import Enum

import requests

import config as config
import loco_validator.validator as loco_validator

cwd = "/tmp/ink_archive"
archive_name = "downloaded.zip"
value_folders = ['values', 'values-de', 'values-es', 'values-fr', 'values-it']

project_root = config.get_project("global", "project_root")


class LocoUpdateStrategy:
    def __init__(self, api_key, copy_target_folder):
        self.api_key = api_key
        self.copy_target_folder = copy_target_folder


def update_loco(target_ids, loco_update_strategy):
    loco_key = loco_update_strategy.api_key
    tag = config.get_project("loco", "tag", raise_error=False) or "android"
    zip_url = f"https://localise.biz/api/export/archive/xml.zip?format=android&filter=${tag}&fallback=en&order=id&key={loco_key}"

    archive_path = download_zip(zip_url)
    if archive_path is None:
        return False

    print("String resources downloaded successfully")

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(cwd)

    os.chdir(cwd)
    files = [file for file in os.listdir('.') if file != archive_name]

    os.chdir(project_root)

    # Copy the strings.xml files from the archive to the project's values folder
    project_path = loco_update_strategy.copy_target_folder
    for value_folder in value_folders:
        target_file = f'{project_path}/{value_folder}/strings.xml'
        source_file = f'{cwd}/{files[0]}/res/{value_folder}/strings.xml'

        shutil.copy(source_file, target_file)

        fix_loco_header(target_file)
        if len(target_ids) > 0:
            remove_unwanted_ids(target_file, target_ids)

    print("String resources updated")

    shutil.rmtree(cwd)
    print("Deleting temporary downloaded strings resources")

    return True


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
    walker = HeaderDiffWalker()
    walker.run(target_file)

    to_replace = "\n".join(walker.added_lines)
    replace_with = "\n".join(walker.removed_lines)
    with open(target_file, "r+") as fd:
        file_content = fd.read()
        fixed_file = file_content.replace(to_replace, replace_with)
        fd.seek(0)
        fd.write(fixed_file)


def remove_unwanted_ids(target_file, target_ids):
    walker = UnwantedIdsDiffWalker()
    walker.run(target_file)

    with open(target_file, "r+") as fd:
        lines = fd.readlines()
        out = ""
        for line in lines:
            if any(line.startswith(added_line) for added_line in walker.added_lines):
                should_keep = any((f'<string name="{target_id}"' in line) for target_id in target_ids)
                if should_keep:
                    out += line
            else:
                out += line

        fd.seek(0)
        fd.write(out)
        fd.truncate()


class DiffWalker:
    def walk(self, line, line_diff_type):
        pass

    def run(self, target_file):
        result = subprocess.run(f"git diff {target_file}", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        diff = result.stdout
        for line in diff.split("\n")[5:]:
            if len(line) == 0:
                continue

            if line[0] == "-":
                returned_value = self.walk(line[1:], LineDiffType.removal)
            elif line[0] == "+":
                returned_value = self.walk(line[1:], LineDiffType.addition)
            else:
                returned_value = self.walk(None, LineDiffType.nothing)

            if returned_value == -1:
                break


class HeaderDiffWalker(DiffWalker):
    def __init__(self):
        self.removed_lines = []
        self.added_lines = []

    def walk(self, line, line_diff_type):
        if line_diff_type == LineDiffType.removal:
            self.removed_lines.append(line)
        elif line_diff_type == LineDiffType.nothing:
            return -1  # break
        else:
            has_header_ended = line.startswith("    <")
            if has_header_ended:
                return -1  # break

            self.added_lines.append(line)


class UnwantedIdsDiffWalker(DiffWalker):
    def __init__(self):
        self.added_lines = []

    def walk(self, line, line_diff_type):
        if line_diff_type == LineDiffType.addition:
            self.added_lines.append(line)


class LineDiffType(Enum):
    addition = 0
    removal = 1
    nothing = 2


def validate_strings(loco_update_strategy):
    error_count = 0

    project_path = loco_update_strategy.copy_target_folder
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
                error_count += loco_validator.validate_string(language, name, value)
            elif tag == "plurals":
                error_count += validate_plural(element, language, name)

    return error_count


def validate_plural(plural, language, name):
    error_count = 0

    for element in plural:
        plural_name = f"{name}-{element.get('quantity')}"
        plural_value = element.text

        error_count += loco_validator.validate_string(language, plural_name, plural_value)

    return error_count
