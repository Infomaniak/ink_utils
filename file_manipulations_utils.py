import os
import subprocess
from enum import Enum, auto


class InsertPosition(Enum):
    """Enum to choose where to insert the line relative to the match."""
    BEFORE = auto()
    AFTER = auto()


def find_first_path(filename, search_path="/"):
    cmd = ["find", search_path, "-type", "f", "-name", filename, "-print", "-quit"]
    result = subprocess.check_output(cmd)
    return result.decode().strip() or None


def insert_line_relative(filepath, line_to_match, line_to_insert, position: InsertPosition):
    """
    Inserts `line_to_insert` relative to the first line whose stripped
    content starts with `line_to_match`, determined by `position`.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inserted = False

    for line in lines:
        # Handle Insert BEFORE
        if position == InsertPosition.BEFORE:
            if not inserted and line.lstrip().startswith(line_to_match):
                # Preserve indentation level of the matched line
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(indent + line_to_insert + "\n")
                inserted = True
            new_lines.append(line)
        # Handle Insert AFTER
        else:
            new_lines.append(line)
            if not inserted and line.lstrip().startswith(line_to_match):
                # preserve indentation level of the matched line
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(indent + line_to_insert + "\n")
                inserted = True

    # Write the updated file
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return inserted


def insert_after_line_or_warn(filepath, line_to_insert, line_to_match):
    is_success = insert_line_relative(
        filepath=filepath,
        line_to_match=line_to_match,
        line_to_insert=line_to_insert,
        position=InsertPosition.AFTER,
    )
    if not is_success:
        print(f"Could not find '{line_to_match}' in {filepath}")


def insert_before_line_or_warn(filepath, line_to_insert, line_to_match):
    is_success = insert_line_relative(
        filepath=filepath,
        line_to_match=line_to_match,
        line_to_insert=line_to_insert,
        position=InsertPosition.BEFORE,
    )
    if not is_success:
        print(f"Could not find '{line_to_match}' in {filepath}")


def find_closest_parent_git_directory(current_directory):
    """
    Walk up the directory tree starting from current_directory
    and return the path to the nearest directory containing a .git folder.

    Returns:
        str | None: Path to the git root directory, or None if not found.
    """
    current_directory = os.path.abspath(current_directory)

    while True:
        git_path = os.path.join(current_directory, ".github")
        if os.path.isdir(git_path):
            return current_directory

        parent_directory = os.path.dirname(current_directory)

        # Stop if we've reached the filesystem root
        if parent_directory == current_directory:
            return None

        current_directory = parent_directory
