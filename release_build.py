import getpass
import os
from pathlib import Path

import config
from utils import run


def build(args):
    projects = [config.get_project("global", "project_root") + "/.."]

    for project in projects:
        keystore_path = config.get_project("build", "keystore_path")
        key_alias = config.get_project("build", "key_alias")
        password = getpass.getpass("Key and keystore passwords:")

        print(f"\n=== Building project: {project} ===")
        try:
            aab_file = build_aab(project)
            sign_aab(aab_file, keystore_path, password, password, key_alias)
            verify_aab(aab_file)
            print(f"Signed AAB ready: {aab_file}\n")

            reveal_in_file_manager(aab_file)
        except Exception as e:
            print(f"Error processing {project}: {e}")


def build_aab(project_dir):
    """Build the release AAB for the given project."""
    gradlew = "./gradlew"
    run([gradlew, "clean", "bundleRelease"], cwd=project_dir)
    aab_dir = Path(project_dir) / "app/build/outputs/bundle/release"
    aab_path = max(aab_dir.glob("*.aab"), key=os.path.getmtime)
    if not aab_path.exists():
        raise FileNotFoundError(f"AAB not found: {aab_path}")
    return aab_path


def sign_aab(aab_path, keystore_path, key_store_pass, key_pass, key_alias):
    """Sign an AAB file with jarsigner."""
    cmd = [
        "jarsigner",
        "-keystore", keystore_path,
        "-storepass", key_store_pass,
        "-keypass", key_pass,
        str(aab_path),
        key_alias
    ]
    run(cmd)


def verify_aab(aab_path):
    """Verify AAB signature."""
    cmd = ["jarsigner", "-verify", "-verbose", "-certs", str(aab_path)]
    run(cmd)


def reveal_in_file_manager(path):
    run(["open", "-R", str(path)])
