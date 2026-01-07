import copy
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requests

import config as config
import loco_validator.validator as loco_validator
from file_manipulations_utils import insert_after_line_or_warn, find_closest_parent_git_directory, insert_before_line_or_warn
from print_utils import color, Colors

loco_tmp_dir = "/tmp/ink_archive"
value_folders = ['values', 'values-de', 'values-es', 'values-fr', 'values-it']

project_root = config.get_project("global", "project_root")

ignored_ids = {
    "appName",  # All apps
    "notification_channel_id_draft_service",  # kMail
    "notification_channel_id_general",  # kMail
    "notification_channel_id_sync_messages_service",  # kMail
    "matomo",  # SwissTransfer
    "sentry",  # SwissTransfer
    "notifications_upload_channel_id",  # SwissTransfer
}


class LocoUpdateStrategy:
    def __init__(self, api_key, copy_target_folder):
        self.api_key = api_key
        self.copy_target_folder = copy_target_folder


def download_strings(loco_update_strategy, input_feature_tag):
    loco_key = loco_update_strategy.api_key
    tag = input_feature_tag or config.get_project("loco", "tag", raise_error=False)
    is_tag_provided = tag is not None

    # Remove ink's tmp folder if it exists because the rest of the code relies on no other files being present
    if os.path.exists(loco_tmp_dir):
        shutil.rmtree(loco_tmp_dir)

    android_archive_name = "android.zip"
    android_archive_path = download_zip(tag="android", loco_key=loco_key, archive_name=android_archive_name)
    if android_archive_path is None:
        return None

    if is_tag_provided:
        tag_archive_name = "tag.zip"
        tag_archive_path = download_zip(tag=tag, loco_key=loco_key, archive_name=tag_archive_name)
        if tag_archive_path is None:
            return None

    print("String resources downloaded successfully")

    android_extraction_folder = loco_tmp_dir + "/android"
    with zipfile.ZipFile(android_archive_path, 'r') as zip_ref:
        zip_ref.extractall(android_extraction_folder)

    if is_tag_provided:
        tag_extraction_folder = loco_tmp_dir + "/tag"
        with zipfile.ZipFile(tag_archive_path, 'r') as zip_ref:
            zip_ref.extractall(tag_extraction_folder)

        output_res_folder = f"{loco_tmp_dir}/merged/res"
        compute_intersection_of_res_folders(android_res_folder=get_res_folder_path(android_extraction_folder),
                                            tag_res_folder=get_res_folder_path(tag_extraction_folder),
                                            output_res_folder=output_res_folder)
    else:
        output_res_folder = get_res_folder_path(android_extraction_folder)

    return output_res_folder  # The path of the res directory


def get_res_folder_path(archive_path):
    return archive_path + "/" + [file for file in os.listdir(archive_path)][0] + "/res"


def compute_intersection_of_res_folders(android_res_folder, tag_res_folder, output_res_folder):
    for folder in value_folders:
        android_xml = f"{android_res_folder}/{folder}/strings.xml"
        tag_xml = f"{tag_res_folder}/{folder}/strings.xml"
        output = f"{output_res_folder}/{folder}/strings.xml"
        compute_intersection_to(android_xml, tag_xml, output)


def compute_intersection_to(first_xml, second_xml, output_file_path):
    """
    Computes the intersection (common keys) of two Android strings XML files and
    writes them to the output file. If the output file does not exist, it is created.

    :param first_xml: Path to the first XML file
    :param second_xml: Path to the second XML file
    :param output_file_path: Path to the output XML file
    """
    register_android_xml_namespaces()

    # Parse input XMLs
    tree_first = ET.parse(first_xml)
    root_first = tree_first.getroot()

    tree_second = ET.parse(second_xml)
    root_second = tree_second.getroot()

    # Build dicts of name -> element for quick lookup
    first_dict = {elem.get('name'): elem for elem in root_first if elem.get('name')}
    second_dict = {elem.get('name'): elem for elem in root_second if elem.get('name')}

    # Intersection of keys present in both files
    common_keys = set(first_dict.keys()) & set(second_dict.keys())

    root_output = ET.Element("resources")

    # Add elements (preserves plurals and nested items)
    for elem in root_first:
        name = elem.get('name')
        if name and name in common_keys:
            root_output.append(copy.deepcopy(elem))

    tree_output = ET.ElementTree(root_output)
    ET.indent(tree_output, space="    ", level=0)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    tree_output.write(output_file_path, encoding="utf-8", xml_declaration=True)


def register_android_xml_namespaces():
    """Register Android XML namespaces to preserve them in output"""
    ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
    ET.register_namespace('tools', 'http://schemas.android.com/tools')
    ET.register_namespace('app', 'http://schemas.android.com/apk/res-auto')


def update_loco(target_ids, loco_update_strategy, extracted_dir_root):
    os.chdir(project_root)

    # Copy the strings.xml files from the archive to the project's values folder
    has_initialized_new_strings = False
    project_path = loco_update_strategy.copy_target_folder
    for value_folder in value_folders:
        target_file_path = f'{project_path}/{value_folder}/strings.xml'
        source_file_path = f'{extracted_dir_root}/{value_folder}/strings.xml'

        target_file = Path(target_file_path)
        if target_file.exists():
            drop_git_diffs_if_any(target_file_path)
        else:
            has_initialized_new_strings = True
            create_empty_file(target_file)

        update_android_strings(current_xml_path=target_file_path, new_xml_path=source_file_path, selected_tags=target_ids,
                               output_xml_path=target_file_path)
        add_missing_new_line_at_end_of(target_file_path)
        fix_loco_header(target_file_path)

    if has_initialized_new_strings:
        add_string_validation_ci_workflow()

    print("String resources updated")


def create_empty_file(file):
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch()
    file.write_text("<resources/>")


def add_string_validation_ci_workflow():
    git_project_directory = find_closest_parent_git_directory(project_root)

    if git_project_directory is None:
        print("Warning: Could not update string validation CI workflow. Do it manually")
        return

    workflow_file = Path(git_project_directory) / ".github" / "workflows" / "translations-validation.yml"
    if not workflow_file.exists():
        print("Warning: Could not update string validation CI workflow. Do it manually")
        return

    workflow_file_path = workflow_file.__str__()

    new_module_config = """TODO_PROJECT_NAME:
            global:
              project_root: "${PR_PATH}/TODO\""""
    insert_after_line_or_warn(workflow_file_path, new_module_config, "cat <<EOF > ink_utils/settings.yml")

    new_validation_task = """- name: Run Ink validation for TODO module
        run: |
          source ink_utils/venv/bin/activate
          python ink_utils/main.py project TODO_PROJECT_NAME
          python ink_utils/main.py loco --check --verbose
"""
    insert_before_line_or_warn(workflow_file_path, new_validation_task, "- name: Run Ink validation")


def remove_downloaded_strings():
    shutil.rmtree(loco_tmp_dir)
    print("Deleting temporary downloaded strings resources")


def compute_project_diffs(loco_update_strategy, extracted_dir_root):
    # needs_to_print_diffs = len(target_ids) > 0 or only_display_diff
    project_path = loco_update_strategy.copy_target_folder

    id_diffs = {}
    for value_folder in value_folders:
        # TODO: Factorize
        target_file = f'{project_path}/{value_folder}/strings.xml'
        source_file = f'{extracted_dir_root}/{value_folder}/strings.xml'

        id_diffs[get_ui_acronym_of(value_folder)] = compute_file_diffs(target_file, source_file)

    pretty_print_diff(id_diffs)


def pretty_print_diff(id_diffs):
    print("\nStatus compared to the remote")
    all_equal = all(v == next(iter(id_diffs.values())) for v in id_diffs.values())
    if all_equal:
        print(next(iter(id_diffs.values())).get_ui_formatted_string())
    else:
        for language, diff in id_diffs.items():
            print(f"[{language}]: {diff.get_ui_formatted_string()}")


def download_zip(tag, loco_key, archive_name):
    zip_url = f"https://localise.biz/api/export/archive/xml.zip?format=android&filter=${tag}&fallback=en&order=id&key={loco_key}"

    response = requests.get(zip_url)

    if response.status_code != 200:
        print("Error: When trying to download translations received response.status_code =", response.status_code)
        return None

    os.makedirs(loco_tmp_dir, exist_ok=True)

    archive_path = loco_tmp_dir + "/" + archive_name
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
    register_android_xml_namespaces()

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
        if (len(selected_tags) == 0 and name not in ignored_ids) or name in selected_tags_set:
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
    ET.indent(tree_current, space="    ", level=0)
    tree_current.write(output_xml_path, encoding="utf-8")


def compute_file_diffs(old_file, new_file):
    return get_id_diffs(root_before=ET.parse(old_file).getroot(), root_after=ET.parse(new_file).getroot())


def get_id_diffs(root_before, root_after):
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
        name for name in common_names if current_map[name] != new_map[name]
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
        to_update = color(self.updated, Colors.blue) if self.updated > 0 else self.updated
        to_remove = color(self.removed, Colors.red) if self.removed > 0 else self.removed
        return f"To add: {to_add}, to updated: {to_update}, to remove: {to_remove}"


def get_ui_acronym_of(value_folder):
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
