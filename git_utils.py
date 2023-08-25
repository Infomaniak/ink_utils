import subprocess


def get_branch_parents(branch):
    log_output = subprocess.run(
        "git log " + branch + ' --decorate=full --simplify-by-decoration --oneline --format="%D"',
        stdout=subprocess.PIPE,
        stderr=None,
        shell=True,
        universal_newlines=True).stdout

    output = []
    for line in log_output.split("\n")[1:]:
        if line.startswith("tag: ") or not line.strip():
            continue

        line = line.replace("HEAD -> ", "")
        line = line.replace("refs/", "")

        branches = line.split(", ")
        current_branch = Branch()
        for branch in branches:
            if branch == "remotes/origin/HEAD":
                continue
            elif branch.startswith("remotes/origin/"):
                current_branch.remote_origin = branch[15:]
            elif branch.startswith("heads/"):
                current_branch.local = branch[6:]

        output.append(current_branch)

    return output


class Branch:
    remote_origin = ""
    local = ""

    def __str__(self):
        return f"(origin: {self.remote_origin}, local: {self.local})"
