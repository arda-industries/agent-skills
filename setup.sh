#!/bin/bash
# Setup script for brain workspace on a new machine
# Run from anywhere after cloning agent-instructions

set -e

BRAIN_DIR="$HOME/brain"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Setting up brain workspace..."

# Create directory structure
mkdir -p "$BRAIN_DIR/git/personal"
mkdir -p "$BRAIN_DIR/git/work"
mkdir -p "$BRAIN_DIR/obsidian"

# Move/link agent-instructions into place if not already there
TARGET_DIR="$BRAIN_DIR/git/personal/agent-instructions"
if [ "$SCRIPT_DIR" != "$TARGET_DIR" ]; then
    if [ -d "$TARGET_DIR" ]; then
        echo "Warning: $TARGET_DIR already exists. Skipping move."
    else
        echo "Moving agent-instructions to $TARGET_DIR"
        mv "$SCRIPT_DIR" "$TARGET_DIR"
        SCRIPT_DIR="$TARGET_DIR"
    fi
fi

# Create .cursorrules pointer
cat > "$BRAIN_DIR/.cursorrules" << 'EOF'
# Cursor Rules (brain workspace)

**Read and follow:** `git/personal/agent-instructions/.cursor/skills/x-brain-workspace-orientation/SKILL.md`

When inside a specific repo under `git/personal/` or `git/work/`, also follow that repo's `.cursorrules` / `AGENTS.md` / `README.md` if present.
EOF

# Create CLAUDE.md pointer
cat > "$BRAIN_DIR/CLAUDE.md" << 'EOF'
# Claude Code (brain workspace)

**Read and follow:** `git/personal/agent-instructions/.cursor/skills/x-brain-workspace-orientation/SKILL.md`

When inside a specific repo under `git/personal/` or `git/work/`, also follow that repo's `.cursorrules` / `AGENTS.md` / `README.md` if present.
EOF

# Symlink skills to brain root for Cursor and Claude Code discovery
SKILLS_SOURCE="$BRAIN_DIR/git/personal/agent-instructions/.cursor/skills"

# .cursor/skills for Cursor
CURSOR_SKILLS_TARGET="$BRAIN_DIR/.cursor/skills"
if [ -L "$CURSOR_SKILLS_TARGET" ]; then
    rm "$CURSOR_SKILLS_TARGET"
fi
mkdir -p "$BRAIN_DIR/.cursor"
ln -sf "$SKILLS_SOURCE" "$CURSOR_SKILLS_TARGET"

# .claude/skills for Claude Code
CLAUDE_SKILLS_TARGET="$BRAIN_DIR/.claude/skills"
if [ -L "$CLAUDE_SKILLS_TARGET" ]; then
    rm "$CLAUDE_SKILLS_TARGET"
fi
mkdir -p "$BRAIN_DIR/.claude"
ln -sf "$SKILLS_SOURCE" "$CLAUDE_SKILLS_TARGET"

echo ""
echo "Setup complete!"
echo ""
echo "Directory structure:"
echo "  $BRAIN_DIR/"
echo "  ├── git/personal/agent-instructions/  (this repo)"
echo "  ├── git/work/"
echo "  ├── obsidian/"
echo "  ├── .cursorrules"
echo "  ├── CLAUDE.md"
echo "  ├── .cursor/skills -> agent-instructions/.cursor/skills"
echo "  └── .claude/skills -> agent-instructions/.cursor/skills"
echo ""
echo "Next steps:"
echo "  1. cd $BRAIN_DIR/git/personal/agent-instructions && poetry install"
echo "  2. Set up API keys in ~/.config/openai/profiles.json and ~/.config/google/profiles.json"
echo "  3. Clone your other repos into git/personal/ or git/work/"
