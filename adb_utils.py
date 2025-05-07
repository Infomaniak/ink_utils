from adb import adb


def get_installed_package_names_in_list(package_names, device_id):
    installed_package_names = []
    for package_name in package_names:
        result = adb(f"shell cmd package list packages {package_name}", device_id).stdout.strip()
        if result.replace("package:", "") == package_name:
            installed_package_names.append(package_name)

    return installed_package_names
