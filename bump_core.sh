#!/bin/bash

set -e

# Usage: ./bump-submodule.sh <submodule-path> <submodule-branch> <new-parent-branch>
SUBMODULE_PATH="Core"
SUBMODULE_BRANCH=$1
NEW_PARENT_BRANCH="bump-core"

if [[ -z "$SUBMODULE_BRANCH" ]]; then
  echo "Usage: $0 <submodule-branch>"
  exit 1
fi

# Navigate to the submodule
cd "$SUBMODULE_PATH"

# Fetch and checkout the desired branch in the submodule
git fetch
git checkout "$SUBMODULE_BRANCH"

# Go back to parent repo
cd -

# Create new branch in parent repo
git checkout -b "$NEW_PARENT_BRANCH"

# Update submodule reference
git add "$SUBMODULE_PATH"
git commit -m "chore: Update core"

echo "✅ Submodule updated and committed on branch '$NEW_PARENT_BRANCH'."
