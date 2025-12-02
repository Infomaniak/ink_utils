import subprocess

import config


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


def insert_after_line_or_warn(filepath, line_to_insert, line_to_match):
    is_success = insert_after_line(
        filepath=filepath,
        line_to_match=line_to_match,
        line_to_insert=line_to_insert,
    )
    if not is_success:
        print(f"Could not find '{line_to_match}' in {filepath}")


def ensure_import(filepath, import_line):
    """
    - Ensures `import_line` exists in the file; adds it if missing.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    already_has_import = any(line.strip() == import_line.strip() for line in lines)

    if not already_has_import:
        import_inserted = False

        for _, line in enumerate(lines):
            new_lines.append(line)

            if not import_inserted:
                stripped = line.strip()

                # Insert after package OR after first import
                if stripped.startswith("package ") or stripped.startswith("import "):
                    new_lines.append(import_line + "\n")
                    import_inserted = True

        # If no appropriate place was found, append at top
        if not import_inserted:
            new_lines.insert(0, import_line + "\n")

    # Write everything back
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def add_preprod_cross_app_login_config(args):
    for project in args.projects:
        project_root = config.get_project_module_parent(project)

        main_app_path = find_first_path("MainApplication.kt", project_root)
        insert_after_line_or_warn(main_app_path, "    apiEnvironment = ApiEnvironment.PreProd,", "NetworkConfiguration.init(")
        ensure_import(main_app_path, "import com.infomaniak.core.network.ApiEnvironment")

        signing_certificates_path = find_first_path("AppSigningCertificates.kt", project_root)
        insert_after_line_or_warn(signing_certificates_path, "true", "acceptedCertificates.any { it.matches(givenSha256) }")
