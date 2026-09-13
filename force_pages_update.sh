#!/bin/bash
set -euo pipefail

repo=$(git rev-parse --show-toplevel)
cd "$repo"
if ! starting_branch=$(git symbolic-ref --quiet --short HEAD); then
    echo "Check out a branch before running this helper; detached HEAD is not supported." >&2
    exit 1
fi
if [[ -n $(git status --porcelain --untracked-files=all) ]]; then
    echo "Commit or stash tracked and untracked changes before running this helper." >&2
    exit 1
fi

# An isolated checkout keeps failures and generated files off the starting branch.
git fetch --no-tags origin refs/heads/gh-pages
pages_commit=$(git rev-parse FETCH_HEAD)
task_dir=$(mktemp -d "${TMPDIR:-/tmp}/winget-pages-update.XXXXXX")
worktree="$task_dir/site"
echo "Pages helper worktree: $worktree (starting branch: $starting_branch)"

finish() {
    status=$?
    trap - EXIT
    if [[ $status -eq 0 ]]; then
        if git -C "$repo" worktree remove "$worktree" && rmdir "$task_dir"; then
            echo "Pages update pushed. Starting branch remains $starting_branch."
            echo "Verify Pages publication and the live site."
        else
            echo "Update pushed, but cleanup failed. Inspect $worktree." >&2
            status=1
        fi
    else
        echo "Pages update failed. Starting branch remains $starting_branch." >&2
        echo "Inspect retained work at $worktree before removing it with git worktree remove." >&2
    fi
    exit "$status"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

git worktree add --detach "$worktree" "$pages_commit"
cd "$worktree"
# Catch a concurrent publication without merging two generated site histories.
git pull --ff-only --no-rebase origin gh-pages
test -f index.html
touch .nojekyll
printf '\n<!-- Pages refresh: %s -->\n' "$(date -u +%FT%TZ)" >> index.html
git add -- .nojekyll index.html
git commit --only -m "chore: trigger Pages publication" -- .nojekyll index.html
git push origin HEAD:refs/heads/gh-pages
cd "$repo"
