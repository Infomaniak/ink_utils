import os
import subprocess


def find_first_path(filename, search_path="/"):
    cmd = ["find", search_path, "-type", "f", "-name", filename, "-print", "-quit"]
    result = subprocess.check_output(cmd)
    return result.decode().strip() or None


def insert_after_line(filepath, line_to_match, line_to_insert):
    """
    Inserts `line_to_insert` on the line immediately after the first line
    whose stripped content starts with `line_to_match`.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)

        # Check if the line matches (ignoring leading spaces)
        if not inserted and line.lstrip().startswith(line_to_match):
            # preserve indentation level of the matched line
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + line_to_insert + "\n")
            inserted = True

    # Write the updated file
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return inserted


def insert_before_line(filepath, line_to_match, line_to_insert):
    """
    Inserts `line_to_insert` on the line immediately before the first line
    whose stripped content starts with `line_to_match`.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inserted = False

    for line in lines:
        # Check if the line matches (ignoring leading spaces)
        if not inserted and line.lstrip().startswith(line_to_match):
            # preserve indentation level of the matched line
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + line_to_insert + "\n")
            inserted = True

        # Add the current line after the check/insertion
        new_lines.append(line)

    # Write the updated file
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return inserted


def insert_after_line_or_warn(filepath, line_to_insert, line_to_match):
    is_success = insert_after_line(
        filepath=filepath,
        line_to_match=line_to_match,
        line_to_insert=line_to_insert,
    )
    if not is_success:
        print(f"Could not find '{line_to_match}' in {filepath}")


def insert_before_line_or_warn(filepath, line_to_insert, line_to_match):
    is_success = insert_before_line(
        filepath=filepath,
        line_to_match=line_to_match,
        line_to_insert=line_to_insert,
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
