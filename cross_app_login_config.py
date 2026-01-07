import config
from file_manipulations_utils import find_first_path, insert_after_line_or_warn


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
