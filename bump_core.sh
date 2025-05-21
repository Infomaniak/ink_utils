#!/bin/bash

set -e

# Usage: ./bump-submodule.sh <submodule-branch>
SUBMODULE_PATH="Core"
SUBMODULE_BRANCH=$1
COMMIT_MESSAGE=${2:-"chore: Bump core"}
NEW_PARENT_BRANCH="bump-core"

if [[ -z "$SUBMODULE_BRANCH" ]]; then
  echo "Usage: $0 <submodule-branch> [commit-message]"
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
git commit -m "$COMMIT_MESSAGE"
git push --set-upstream origin "$NEW_PARENT_BRANCH"

echo "✅ Submodule updated and committed on branch '$NEW_PARENT_BRANCH'."


# Detect base branch (main or master)
if git show-ref --verify --quiet refs/remotes/origin/main; then
  BASE_BRANCH="main"
elif git show-ref --verify --quiet refs/remotes/origin/master; then
  BASE_BRANCH="master"
else
  echo "❌ Could not determine base branch (main or master)."
  exit 1
fi

# Get remote GitHub URL
REPO_URL=$(git config --get remote.origin.url)

# Convert to GitHub web URL
REPO_WEB=$(echo "$REPO_URL" | sed -E 's#git@github.com:(.*)\.git#https://github.com/\1#' | sed -E 's#https://github.com/(.*)\.git#https://github.com/\1#')

# Create PR URL
PR_URL="$REPO_WEB/compare/$NEW_PARENT_BRANCH?expand=1&body=Depends+on+&labels=enhancement"

# Wait for push to have taken effect so opening the url in browser correctly displays instantly
sleep 1
# Open in browser (macOS only)
open "$PR_URL"

echo "🌐 Opened PR page for '$NEW_PARENT_BRANCH' against '$BASE_BRANCH':"
echo "$PR_URL"