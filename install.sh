#!/usr/bin/env bash
set -euo pipefail
target=codex
dest=
repo=WaytoAIC/waytoaic-review-to-opportunity
ref=main
while (($#)); do
  case "$1" in
    --target|--dest|--repo|--ref)
      (($# >= 2)) || { echo "Missing value for $1" >&2; exit 2; }
      case "$1" in --target) target=$2;; --dest) dest=$2;; --repo) repo=$2;; --ref) ref=$2;; esac
      shift 2;;
    *) echo "Unknown argument: $1" >&2; exit 2;;
  esac
done
case "$target" in
  codex) base="${CODEX_HOME:-$HOME/.codex}/skills";;
  openclaw) base="$HOME/.openclaw/skills";;
  *) echo "Target must be codex or openclaw" >&2; exit 2;;
esac
dest=${dest:-$base/waytoaic-review-to-opportunity}
[[ ! -e "$dest" && ! -L "$dest" ]] || { echo "Destination exists: $dest" >&2; exit 1; }
[[ "$ref" != -* && "$repo" != -* ]] || exit 2
if [[ -d "$repo" ]]; then source_repo=$repo
elif [[ "$repo" =~ ^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$ ]]; then source_repo="https://github.com/$repo.git"
else echo "Use owner/repo or a local repository directory" >&2; exit 2
fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
git clone --quiet --depth 1 --branch "$ref" -- "$source_repo" "$tmp/source"
[[ -f "$tmp/source/SKILL.md" ]] || { echo "Missing SKILL.md" >&2; exit 1; }
mkdir -p "$(dirname "$dest")"
mkdir "$dest"
for item in SKILL.md agents references scripts assets; do
  cp -R "$tmp/source/$item" "$dest/$item"
done
printf 'Installed %s to %s\n' "$ref" "$dest"
