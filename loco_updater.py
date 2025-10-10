import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from enum import Enum

import requests

import config as config
import loco_validator.validator as loco_validator
from print_utils import color, Colors

cwd = "/tmp/ink_archive"
archive_name = "downloaded.zip"
value_folders = ['values', 'values-de', 'values-es', 'values-fr', 'values-it']

project_root = config.get_project("global", "project_root")


class LocoUpdateStrategy:
    def __init__(self, api_key, copy_target_folder):
        self.api_key = api_key
        self.copy_target_folder = copy_target_folder


def update_loco(target_ids, loco_update_strategy, input_feature_tag):
    loco_key = loco_update_strategy.api_key
    android_tag = "android"
    main_tag_to_query = android_tag
    feature_tag = input_feature_tag or config.get_project("loco", "tag", raise_error=False)

    tags_to_filter_out = None
    if not (feature_tag is None):
        tags = list_tags(loco_key)
        tags.remove(android_tag)
        tags.remove("ios")
        tags.remove("ios-stringsdict")
        tags.remove(feature_tag)
        tags_to_filter_out = tags
        main_tag_to_query = feature_tag

    # Remove ink's tmp folder if it exists because the rest of the code relies on no other files being present
    if os.path.exists(cwd):
        shutil.rmtree(cwd)

    archive_path = download_zip(main_tag_to_query, loco_key, tags_to_filter_out)
    if archive_path is None:
        return False

    print("String resources downloaded successfully")

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(cwd)

    os.chdir(cwd)
    files = [file for file in os.listdir('.') if file != archive_name]

    os.chdir(project_root)

    # Copy the strings.xml files from the archive to the project's values folder
    id_diffs = {}
    project_path = loco_update_strategy.copy_target_folder
    for value_folder in value_folders:
        target_file = f'{project_path}/{value_folder}/strings.xml'
        source_file = f'{cwd}/{files[0]}/res/{value_folder}/strings.xml'

        fix_xml_indent_of_file_to(source_file, 4)

        drop_git_diffs_if_any(target_file)

        id_diff = update_android_strings(current_xml_path=target_file, new_xml_path=source_file, selected_tags=target_ids,
                                         output_xml_path=target_file)
        id_diffs[get_ui_acronym(value_folder)] = id_diff

        add_missing_new_line_at_end_of(target_file)

        fix_loco_header(target_file)

    print("String resources updated")

    shutil.rmtree(cwd)
    print("Deleting temporary downloaded strings resources")

    # Print status of the imported project compared to the remote when selecting only certain ids by hand
    if len(target_ids) > 0:
        print("\nStatus compared to the remote")
        all_equal = all(v == next(iter(id_diffs.values())) for v in id_diffs.values())
        if all_equal:
            print(next(iter(id_diffs.values())).get_ui_formatted_string())
        else:
            for language, diff in id_diffs.items():
                print(f"[{language}]: {diff.get_ui_formatted_string()}")

    return True


def list_tags(loco_key):
    api_url = "https://localise.biz/api/tags"
    headers = {"Authorization": f"Loco {loco_key}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def download_zip(main_tag, loco_key, tags_to_filter_out):
    negative_tags_query = join_to_string(tags_to_filter_out)
    zip_url = f"https://localise.biz/api/export/archive/xml.zip?format=android&filter=${main_tag}${negative_tags_query}&fallback=en&order=id&key={loco_key}"

    archive_path = cwd + "/" + archive_name

    response = requests.get(zip_url)

    if response.status_code != 200:
        print("Error: When trying to download translations received response.status_code =", response.status_code)
        return None

    os.makedirs(cwd, exist_ok=True)

    with open(archive_path, "wb+") as f:
        f.write(response.content)

    return archive_path


def join_to_string(item_list):
    if not item_list or any(item is None for item in item_list):
        return ""
    else:
        return ',' + ','.join(f"!{item}" for item in item_list)


def drop_git_diffs_if_any(target_file):
    relative_path = target_file[len(project_root) + 1:]
    subprocess.run(["git", "restore", "--", relative_path], cwd=project_root, check=True)


def update_android_strings(current_xml_path, new_xml_path, selected_tags, output_xml_path):
    """
    :param selected_tags: If empty, all modifications will be applied
    :return: Stat object containing info what differences have been observed
    """

    never_remove_ids = {
        "appName",  # All apps
        "notification_channel_id_draft_service",  # kMail
        "notification_channel_id_general",  # kMail
        "notification_channel_id_sync_messages_service"  # kMail
    }

    ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
    ET.register_namespace('tools', 'http://schemas.android.com/tools')
    ET.register_namespace('app', 'http://schemas.android.com/apk/res-auto')

    # Parse both XML files
    tree_current = ET.parse(current_xml_path)
    root_current = tree_current.getroot()

    tree_new = ET.parse(new_xml_path)
    root_new = tree_new.getroot()

    # Convert selected_tags list to set for faster lookup
    selected_tags_set = set(selected_tags)

    # Remove all selected tags from the current root
    for elem in list(root_current):
        name = elem.get('name')
        if (len(selected_tags) == 0 and name not in never_remove_ids) or name in selected_tags_set:
            root_current.remove(elem)

    # Insert selected tags in the order they appear in the new XML
    for elem in root_new:
        name = elem.get('name')
        if len(selected_tags) == 0 or name in selected_tags_set:
            root_current.append(elem)

    # Separate translatable="false" tags (keep in original order)
    non_translatable_elems = [e for e in root_current if e.get('translatable') == 'false']
    translatable_elems = [e for e in root_current if e.get('translatable') != 'false']

    # Sort only the translatable ones alphabetically by name
    translatable_elems.sort(key=lambda e: e.get('name') or "")

    # Combine back (non-translatable first, sorted translatable after)
    root_current[:] = non_translatable_elems + translatable_elems

    # Save the updated XML file
    tree_current.write(output_xml_path, encoding="utf-8")

    return get_id_diffs(root_before=root_current, root_after=root_new, ignored_ids=never_remove_ids)


def get_id_diffs(root_before, root_after, ignored_ids):
    # Build lookup maps by name for both XML roots
    current_map = {
        elem.get('name'): (elem.text or "").strip()
        for elem in root_before if elem.get('name')
    }
    new_map = {
        elem.get('name'): (elem.text or "").strip()
        for elem in root_after if elem.get('name')
    }

    current_names = set(current_map.keys())
    new_names = set(new_map.keys())

    # Compute sets
    added_names = new_names - current_names
    removed_names = current_names - new_names
    common_names = current_names & new_names

    # Exclude never_remove_ids
    added_names -= ignored_ids
    removed_names -= ignored_ids
    common_names -= ignored_ids

    # Compute updated (content-changed) entries
    updated_names = {
        name for name in common_names
        if current_map[name] != new_map[name]
    }

    return IdDiff(
        added=len(added_names),
        removed=len(removed_names),
        updated=len(updated_names),
    )


@dataclass
class IdDiff:
    added: int = 0
    removed: int = 0
    updated: int = 0

    def get_ui_formatted_string(self):
        to_add = color(self.added, Colors.green) if self.added > 0 else self.added
        to_update = color(self.updated, Colors.blue) if self.added > 0 else self.updated
        to_remove = color(self.removed, Colors.red) if self.added > 0 else self.removed
        return f"To add: {to_add}, to updated: {to_update}, to remove: {to_remove}"


def fix_xml_indent_of_file_to(target_file, indent_amount):
    """
    Parses an XML file, re-indents it with the given indentation amount,
    and writes it back to the same file.

    Args:
        target_file (str | Path): Path to the XML file.
        indent_amount (int): Number of spaces for indentation.
    """
    tree = ET.parse(target_file)
    ET.indent(tree, space=" " * indent_amount)
    tree.write(target_file, encoding="utf-8", xml_declaration=True)


def get_ui_acronym(value_folder):
    parts = value_folder.split('-')
    return parts[-1] if len(parts) > 1 else 'en'


def add_missing_new_line_at_end_of(target_file):
    # It's ok to assume the file only contains characters in utf-8
    with open(target_file, "rb+") as f:
        f.seek(-1, 2)  # go to the last byte
        if f.read(1) != b'\n':  # check if it's not a newline
            f.write(b'\n')  # add one if missing


def fix_loco_header(target_file):
    walker = HeaderDiffWalker()
    walker.run(target_file)

    replace_with = "\n".join(walker.removed_lines)

    with open(target_file, "r") as fd:
        original_content = fd.read()

    with open(target_file, "w") as fd:
        fd.write(replace_with + "\n" + original_content)

    if len(walker.added_lines) > 0:
        print("Warning: When trying to bring back the previous header, an unexpected diff with added lines has been detected")


class DiffWalker:
    def walk(self, line, line_diff_type):
        pass

    def run(self, target_file):
        # -U0 forces the git diff to have zero padding lines around the diff to avoid breaking the detection
        result = subprocess.run(f"git diff -U0 {target_file}", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
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
