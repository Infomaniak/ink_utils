import config


def list_projects():
    projects = config.list_projects()
    for project in projects:
        prefix = " * " if project == config.project_key else "   "
        print(f"{prefix} {project}")


def select_project(project_name):
    if project_name in config.list_projects():
        with open(config.current_project_file, "w") as f:
            f.write(project_name)
    else:
        print(f"No project named {project_name} specified in {config.config_filename}")
