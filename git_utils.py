import os
import subprocess
from anytree import Node

import config as config


def get_local_branches():
    repo_location = config.get("loco", "project_root", ".") + "/../"

    local_branches = subprocess.run(
        "git for-each-ref --format='%(refname:short)' refs/heads/",
        stdout=subprocess.PIPE,
        stderr=None,
        shell=True,
        universal_newlines=True
    ).stdout.split("\n")

    targeted_branches = find_targets(repo_location)

    nodes = {}
    for local_branch in local_branches:
        genealogy = get_branch_parents(local_branch)
        print(" => " + local_branch)
        for ancestor in genealogy:
            print(str(ancestor))

        print()

    return nodes


def find_targets(repo_location):
    with open(repo_location + ".git/config", "r") as f:
        config_lines = f.readlines()

    targets = {}
    i = 0
    while i < len(config_lines):
        line = config_lines[i]

        if line.startswith('[branch "'):
            remote_branch_name = line[9:-2]

            config_remote = config_lines[i + 1].strip()
            if config_remote != "remote = origin":
                print("Found a remote branch who's not on 'origin', this is not handled")
                return None

            remote = "refs/remotes/origin/" + remote_branch_name

            config_merge = config_lines[i + 2].strip()
            local = config_merge[8:]

            targets[local] = remote

            i += 2

        i += 1

    return targets


# TODO : doesnt give list of all parents correctly, find out why
def get_branch_parents(branch):
    log_output = subprocess.run(
        "git log " + branch + ' --decorate=full --simplify-by-decoration --oneline --format="%D"',
        stdout=subprocess.PIPE,
        stderr=None,
        shell=True,
        universal_newlines=True
    ).stdout

    output = []
    for line in log_output.split("\n")[1:]:
        if line.startswith("tag: ") or not line.strip():
            continue

        print(line)

        line = line.replace("HEAD -> ", "")

        branches = line.split(", ")
        current_branch = Branch()
        for branch in branches:
            if branch == "remotes/origin/HEAD":
                continue
            elif branch.startswith("refs/remotes/origin/"):
                current_branch.remote_origin = branch
            elif branch.startswith("refs/heads/"):
                current_branch.local = branch

        output.append(current_branch)

    return output


class Branch:
    remote_origin = ""
    local = ""

    def __init__(self, remote_origin="", local=""):
        self.remote_origin = remote_origin
        self.local = local

    def __str__(self):
        return f"(origin: {self.remote_origin}, local: {self.local})"

    def __ref__(self):
        return f"Branch({self.remote_origin}, {self.local})"
