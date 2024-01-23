import subprocess


def run_cmd(cmd):
    out = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    return out.stdout


def does_current_branch_target_main():
    return run_cmd("git rev-parse --abbrev-ref HEAD@{upstream}").startswith("origin/main")


def get_current_branch_hash():
    return run_cmd("git rev-parse HEAD")


def get_remote_main_hash():
    return run_cmd("git fetch && git rev-parse origin/main")


def check_for_updates():
    if does_current_branch_target_main():
        current_hash = get_current_branch_hash()
        latest_hash = get_remote_main_hash()

        if current_hash != latest_hash:
            print("A new version of Ink is available!\n")
