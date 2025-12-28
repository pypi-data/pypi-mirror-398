import click
import subprocess
import sys
from pathlib import Path
from .scanner import scan_files
from .installer import install_hook, uninstall_hook

def get_staged_files():
    """Return list of staged files' paths."""
    res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
    if res.returncode != 0:
        return []
    out = res.stdout.strip()
    if not out:
        return []
    return [p for p in out.splitlines() if p.strip()]

@click.group()
def cli():
    """ShieldCommit - Secret Scanner for Git Commits"""
    pass

@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=False))
def scan(paths):
    """
    Scan staged files (default) or provided files/directories.
    Usage:
      shieldcommit scan            # scans staged files
      shieldcommit scan file1.py   # scans specific file(s)
      shieldcommit scan dir/       # scans all files in dir (if SCAN_ALL=1 or path provided)
    """
    # if paths provided, scan them; else scan staged files
    if paths:
        # expand directories to files
        to_scan = []
        for p in paths:
            pth = Path(p)
            if pth.is_dir():
                for f in pth.rglob("*"):
                    if f.is_file():
                        to_scan.append(str(f))
            else:
                to_scan.append(str(pth))
    else:
        to_scan = get_staged_files()
        if not to_scan:
            click.echo("No staged files. Use `shieldcommit scan <paths>` to scan files or set staged files.")
            sys.exit(0)

    result = scan_files(to_scan)
    findings = result["findings"]
    warnings = result["warnings"]
    
    # Display warnings (non-blocking)
    if warnings:
        click.echo("⚠️  VERSION WARNINGS (Info only - no block):\n")
        for w in warnings:
            click.echo(f"File: {w['file']} (line {w['line']})")
            click.echo(f"  {w['message']}")
            click.echo(f"  Snippet: {w['snippet']}")
            click.echo("")
    
    # Display findings (blocking)
    if not findings:
        click.echo("✓ No secrets found.")
        sys.exit(0)

    click.echo("❌ Secrets detected!\n")
    for f in findings:
        click.echo(f"File: {f['file']} (line {f['line']})")
        click.echo(f"  Pattern: {f['pattern']}")
        click.echo(f"  Snippet: {f['snippet']}")
        click.echo("")
    click.echo("Your commit or action has been blocked. Remove or rotate secrets before proceeding.")
    sys.exit(1)

@cli.command()
def install():
    """Install pre-commit hook in current repo."""
    ok = install_hook(".")
    if ok:
        click.echo("✅ ShieldCommit hook installed.")
    else:
        click.echo("❌ Failed to install hook.")

@cli.command()
def uninstall():
    ok = uninstall_hook(".")
    if ok:
        click.echo("🗑️ ShieldCommit hook removed.")
    else:
        click.echo("Hook not found.")
