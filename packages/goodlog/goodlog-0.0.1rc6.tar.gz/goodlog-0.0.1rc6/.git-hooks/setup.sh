#!/bin/zsh

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Setting up git hooks..."

echo "Copying pre-commit script from '$REPO_ROOT/.git-hooks/pre-commit' to '$HOOKS_DIR/pre-commit'"
cp "$REPO_ROOT/.git-hooks/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Git hooks set up successfully!"

echo "To bypass hooks for a specific commit, use:"
echo "  git commit --no-verify"
