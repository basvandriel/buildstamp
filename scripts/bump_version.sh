#!/usr/bin/env bash
# Usage: scripts/bump_version.sh [patch|minor|major]
#
# Reads VERSION, computes the new version, and writes it back (when bumped).
# When run inside GitHub Actions, also writes version/tag/bumped to GITHUB_OUTPUT.
set -euo pipefail

BUMP="${1:-none}"
CURRENT="$(cat VERSION)"
MAJOR="$(echo "$CURRENT" | cut -d. -f1)"
MINOR="$(echo "$CURRENT" | cut -d. -f2)"
PATCH="$(echo "$CURRENT" | cut -d. -f3)"

case "$BUMP" in
  major) VERSION="$((MAJOR+1)).0.0" ;;
  minor) VERSION="${MAJOR}.$((MINOR+1)).0" ;;
  patch) VERSION="${MAJOR}.${MINOR}.$((PATCH+1))" ;;
  *) echo "Unknown bump type: $BUMP (use patch|minor|major)" >&2; exit 1 ;;
esac

if [[ "$VERSION" != "$CURRENT" ]]; then
  echo "$VERSION" > VERSION
  echo "Bumped $BUMP: $CURRENT → $VERSION"
  BUMPED=true
else
  echo "No bump — current version: $VERSION"
  BUMPED=false
fi

# Write GitHub Actions step outputs when running in CI
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "version=$VERSION"
    echo "tag=v$VERSION"
    echo "bumped=$BUMPED"
  } >> "$GITHUB_OUTPUT"
fi
