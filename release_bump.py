import re
import subprocess
from enum import Enum
from pathlib import Path

import config
from utils import run

BRANCH_PREFIX = "bump-"  # new branch name prefix, e.g. bump-3.4.0


def bump(args):
    module_path = config.get_project("global", "project_root")
    project_git_root = module_path + "/.."

    build_gradle = find_build_gradle(module_path)
    text = build_gradle.read_text()

    _, version_name = parse_version_info(text)
    new_version_name = bump_version_name(version_name, args.type)
    new_version_code = bump_version_code(new_version_name)

    update_build_gradle(build_gradle, new_version_code, new_version_name)
    print(f"✅ Updated {build_gradle}:")
    print(f"   versionCode {new_version_code}")
    print(f"   versionName '{new_version_name}'")

    git_commit_and_branch(new_version_name, project_git_root)


def find_build_gradle(module_root):
    """Locate the app/build.gradle file."""
    build_gradle = Path(module_root) / "build.gradle"
    if not build_gradle.exists():
        raise FileNotFoundError(f"Could not find {build_gradle}")
    return build_gradle


def parse_version_info(text):
    """Extract versionCode and versionName from Gradle text."""
    code_match = re.search(r"versionCode\s+([0-9_]+)", text)
    name_match = re.search(r"versionName\s+'([\d.]+)'", text)

    if not code_match or not name_match:
        raise ValueError("Could not find versionCode or versionName in build.gradle")

    version_code = code_match.group(1)
    version_name = name_match.group(1)
    return version_code, version_name


def bump_version_name(version_name, level):
    """Increment semantic version (major.minor.patch)."""
    parts = [int(p) for p in version_name.split(".")]
    while len(parts) < 3:
        parts.append(0)

    if level == BumpType.major:
        parts[0] += 1
        parts[1], parts[2] = 0, 0
    elif level == BumpType.minor:
        parts[1] += 1
        parts[2] = 0
    elif level == BumpType.patch:
        parts[2] += 1
    else:
        raise ValueError("Level must be 'major', 'minor', or 'patch'")

    return ".".join(str(p) for p in parts)


def bump_version_code(new_version_name=None):
    """
    Build versionCode in format MAJOR_MINOR_PATCH_01
    Example:
        versionName '3.4.2' -> versionCode 3_04_002_01
    The rightmost value is always hardcoded to 01.
    """
    if not new_version_name:
        raise ValueError("new_version_name must be provided to generate versionCode")

    parts = [int(p) for p in new_version_name.split(".")]
    while len(parts) < 3:
        parts.append(0)

    major, minor, patch = parts
    return f"{major}_{minor:02d}_{patch:03d}_01"


def update_build_gradle(file_path, new_code, new_name):
    """Replace versionCode and versionName lines."""
    text = file_path.read_text()
    text = re.sub(r"versionCode\s+[0-9_]+", f"versionCode {new_code}", text)
    text = re.sub(r"versionName\s+'[\d.]+'", f"versionName '{new_name}'", text)
    file_path.write_text(text)


def get_default_branch(git_project_root):
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        capture_output=True,
        text=True,
        cwd=git_project_root,
    )
    return result.stdout.strip().split("/")[-1] if result.returncode == 0 else "main"


def git_commit_and_branch(new_version, git_project_root):
    """Commit and push version bump on a new branch."""
    branch_name = f"{BRANCH_PREFIX}{new_version}"

    # Update main and create new branch
    default_branch = get_default_branch(git_project_root)
    run(["git", "checkout", default_branch], cwd=git_project_root)
    run(["git", "pull", "origin", default_branch], cwd=git_project_root)
    run(["git", "checkout", "-b", branch_name], cwd=git_project_root)

    # Stage and commit
    run(["git", "add", "."], cwd=git_project_root)
    run(["git", "commit", "-m", f"chore(Version): {new_version}"], cwd=git_project_root)
    run(["git", "push", "-u", "origin", branch_name], cwd=git_project_root)

    print(f"✅ Created and pushed branch: {branch_name}")


class BumpType(Enum):
    major = "major"
    minor = "minor"
    patch = "patch"

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return BumpType[s]
        except KeyError:
            raise ValueError()
