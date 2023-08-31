from git_utils import get_local_branches


def open_pr(branch):
    branches = get_local_branches()
    for branch in branches:
        print(str(branch))
