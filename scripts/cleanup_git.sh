#!/usr/bin/env bash
# Safe helper to remove committed virtualenv and outputs from git cache
# Run from the repository root. This script only stages removal and updates .gitignore.

set -euo pipefail

echo "Ensure you're in the repository root and have a clean working tree before running this."
read -p "Continue? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 1
fi

# Update .gitignore is already done. Stage the .gitignore change if present
git add .gitignore || true

# Remove common large directories from the index (safe if listed in .gitignore)
for d in venv .venv ENV env outputs; do
  if git ls-files --error-unmatch "$d" >/dev/null 2>&1; then
    echo "Removing $d from git index..."
    git rm -r --cached "$d" || true
  else
    echo "No tracked $d found or not a git repo entry."
  fi
done

# Remove pycache and coverage artifacts from index if present
git rm -r --cached __pycache__ || true
git rm --cached .coverage || true

echo "Done. Review changes with 'git status' and commit when ready."

echo "Suggested commit: git commit -m 'chore: remove virtualenv and outputs from repo; update .gitignore'"
