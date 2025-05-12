#!/bin/bash

# When called with no argument, this script will print the list of PRs that have been merged since the biggest version number 
# present in the tags. When called with an argument, it will take this reference as the starting point to list merged PRs.

# Optional argument: starting point (e.g., a tag or SHA)
START_REF=${1}

# If not provided, fall back to latest version tag
if [ -z "$START_REF" ]; then
  START_REF=$(git tag | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n 1)
fi

# Searches for remote main or master's SHA
LATEST_MASTER_SHA=$(git ls-remote --heads origin main master | awk '/refs\/heads\/main/ {print "main", $1; exit} /refs\/heads\/master/ {print "master", $1; exit}' | awk '{print $2}')

# Get merge commit messages
PR_MESSAGES=$(git log --merges $START_REF..$LATEST_MASTER_SHA --pretty=format:"%s")

# Remove prefix like "fix(scope): " or "feat: " and trailing "(#1234)"
clean_message() {
  sed -E 's/^[a-zA-Z]+(\([^)]+\))?:[ ]*//' | sed -E 's/[[:space:]]*\(#([0-9]+)\)[[:space:]]*$//'
}

# Prints cleaned messages by tag (wraps raw method + clean)
print_cleaned_messages_by_tag() {
  TAG="$1"
  echo "$PR_MESSAGES" | grep -E "^$TAG(\([^)]+\))?:" | clean_message
}

echo "Merged PRs on master since: $START_REF"

echo ""
echo "Features:"
print_cleaned_messages_by_tag "feat" || echo "(none)"

echo ""
echo "Fixes:"
print_cleaned_messages_by_tag "fix" || echo "(none)"

echo ""
echo "Other:"
echo "$PR_MESSAGES" | grep -vE '^(feat|fix)(\([^)]+\))?:' || echo "(none)"
