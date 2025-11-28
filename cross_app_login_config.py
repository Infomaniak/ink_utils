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


def add_preprod_cross_app_login_config(args):
    project_root = config.get_project_module_parent()

    main_application_path = find_first_path("MainApplication.kt", project_root)
    insert_after_line(
        filepath=main_application_path,
        line_to_match="NetworkConfiguration.init(",
        line_to_insert="    apiEnvironment = ApiEnvironment.PreProd,"
    )

    app_signing_path = find_first_path("AppSigningCertificates.kt", project_root)
    insert_after_line(
        filepath=app_signing_path,
        line_to_match="acceptedCertificates.any { it.matches(givenSha256) }",
        line_to_insert="true"
    )
