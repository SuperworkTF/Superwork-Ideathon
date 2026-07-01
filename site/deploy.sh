#!/usr/bin/env bash
# Rebuild detail pages and deploy site/ to the gh-pages branch.
# Usage:  bash site/deploy.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"       # .../site
REPO="$(cd "$DIR/.." && pwd)"
WT="$REPO/.ghpages-wt"

node "$DIR/build.cjs"

git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true
rm -rf "$WT"
git -C "$REPO" fetch origin gh-pages >/dev/null 2>&1 || true

if git -C "$REPO" show-ref --verify --quiet refs/heads/gh-pages || \
   git -C "$REPO" ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  git -C "$REPO" worktree add "$WT" gh-pages
else
  git -C "$REPO" worktree add --detach "$WT" HEAD
  git -C "$WT" checkout --orphan gh-pages
fi

git -C "$WT" rm -rf . >/dev/null 2>&1 || true
cp -R "$DIR"/. "$WT"/
rm -f "$WT/build.cjs" "$WT/deploy.sh" "$WT/README.md"

git -C "$WT" add -A
if git -C "$WT" commit -q -m "site: update $(date -u +%FT%TZ)"; then
  git -C "$WT" push origin gh-pages
  echo "deployed → https://superworktf.github.io/Superwork-Ideathon/"
else
  echo "no changes to deploy"
fi
git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true
