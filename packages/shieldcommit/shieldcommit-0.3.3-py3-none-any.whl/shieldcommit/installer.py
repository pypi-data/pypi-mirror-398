from pathlib import Path

HOOK_TEMPLATE = """#!/bin/bash
# ShieldCommit pre-commit hook
# This calls the shieldcommit CLI to scan staged files
shieldcommit scan
RESULT=$?
if [ $RESULT -ne 0 ]; then
  echo "ShieldCommit: commit blocked due to detected secrets."
  exit 1
fi
exit 0
"""

def install_hook(repo_path='.'):
    git_hooks = Path(repo_path) / '.git' / 'hooks'
    git_hooks.mkdir(parents=True, exist_ok=True)
    hook_file = git_hooks / 'pre-commit'
    hook_file.write_text(HOOK_TEMPLATE)
    hook_file.chmod(0o755)
    return True

def uninstall_hook(repo_path='.'):
    hook_file = Path(repo_path) / '.git' / 'hooks' / 'pre-commit'
    if hook_file.exists():
        hook_file.unlink()
        return True
    return False
