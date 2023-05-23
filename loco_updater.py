import os
import shutil

import configparser
import subprocess
import requests
import zipfile

script_folder = os.path.dirname(__file__)
config_filename = "settings.txt"
config_file = script_folder + '/' + config_filename
missing_config_file = True

if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read_file(open(config_file))
    loco_key = config.get('loco', 'loco_key')
    zip_url = f"https://localise.biz/api/export/archive/xml.zip?format=android&filter=android&fallback=en&order=id&key={loco_key}"

    project_root = config.get('loco', 'project_root')
    project_path = project_root + "/src/main/res"
    missing_config_file = False

cwd = "/tmp/ink_archive"
archive_name = "downloaded.zip"
value_folders = ['values', 'values-de', 'values-es', 'values-fr', 'values-it']


def update_loco():
    if missing_config_file:
        print(f"Missing {config_filename} file at {script_folder}")
        return

    archive_path = download_zip()
    if archive_path is None:
        return

    print("String resources downloaded successfully")

    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(cwd)

    os.chdir(cwd)
    files = os.listdir('.')

    os.chdir(project_root)

    # Copy the strings.xml files from the archive to the project's values folder
    for value_folder in value_folders:
        target_file = f'{project_path}/{value_folder}/strings.xml'
        source_file = f'{cwd}/{files[0]}/res/{value_folder}/strings.xml'

        shutil.copy(source_file, target_file)

        fix_loco_header(target_file)

    print("String resources updated")

    shutil.rmtree(cwd)
    print("Deleting temporary downloaded strings resources")


def download_zip():
    archive_path = cwd + "/" + archive_name

    response = requests.get(zip_url)

    if response.status_code != 200:
        print("Error: When trying to download translations received response.status_code =", response.status_code)
        return None

    os.makedirs(cwd, exist_ok=True)

    with open(archive_path, "wb+") as f:
        f.write(response.content)

    return archive_path


def fix_loco_header(target_file):
    result = subprocess.run(f"git diff {target_file}", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    diff = result.stdout
    removed_lines = []
    added_lines = []
    for line in diff.split("\n")[5:]:
        if line[0] == "-":
            removed_lines.append(line[1:])
        elif line[0] == "+":
            added_lines.append(line[1:])
        else:
            break
    to_replace = "\n".join(added_lines)
    replace_with = "\n".join(removed_lines)
    with open(target_file, "r+") as fd:
        file_content = fd.read()
        fixed_file = file_content.replace(to_replace, replace_with)
        fd.seek(0)
        fd.write(fixed_file)
