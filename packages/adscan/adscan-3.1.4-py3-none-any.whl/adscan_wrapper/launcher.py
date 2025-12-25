import sys
import os
from importlib.resources import files

ADSCAN_SUDO_ALIAS_MARKER = "# ADscan auto-sudo alias"


def _remove_legacy_adscan_sudo_alias(rcfile: str) -> bool:
    """Remove the legacy ADscan auto-sudo alias from a shell rc file.

    Older versions of this launcher injected:

        # ADscan auto-sudo alias
        alias adscan='sudo -E ...'

    This is now harmful because it forces ADscan to run as root (and preserve
    environment), which can lead to permission issues and state divergence.

    The cleanup is intentionally conservative: it only removes the exact marker
    line plus the following alias line when it matches the previous pattern.

    Args:
        rcfile: Path to the rc file to edit in-place.

    Returns:
        True if the file was modified.
    """
    try:
        if not os.path.exists(rcfile):
            return False

        with open(rcfile, "r", encoding="utf-8") as f:
            lines = f.readlines()

        changed = False
        new_lines: list[str] = []
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line.strip() == ADSCAN_SUDO_ALIAS_MARKER.strip():
                next_idx = idx + 1
                if next_idx < len(lines) and lines[next_idx].lstrip().startswith(
                    "alias adscan='sudo -E "
                ):
                    changed = True
                    idx += 2
                    continue
            new_lines.append(line)
            idx += 1

        if not changed:
            return False

        with open(rcfile, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True
    except Exception:
        # Best-effort cleanup; never fail launch because of rc file edits.
        return False


def _cleanup_legacy_sudo_alias() -> None:
    """Best-effort removal of the legacy auto-sudo alias from user shell configs."""
    is_sudo = "SUDO_USER" in os.environ
    if os.geteuid() == 0 and is_sudo:
        target_user = os.environ.get("SUDO_USER")
    else:
        target_user = os.environ.get("USER")

    if target_user:
        home = os.path.expanduser(f"~{target_user}")
    else:
        home = os.path.expanduser("~")

    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rcfiles = [os.path.join(home, ".zshrc")]
    else:
        # Older launcher used .bash_aliases; also check .bashrc just in case.
        rcfiles = [os.path.join(home, ".bash_aliases"), os.path.join(home, ".bashrc")]

    for rcfile in rcfiles:
        _remove_legacy_adscan_sudo_alias(rcfile)

def main():
    # --- PIPX EXECUTION BLOCK ---
    # This is the most reliable way to prevent usage from a pipx environment.
    # We check at runtime, not during the unpredictable installation process.
    # if 'pipx' in sys.prefix:
    #     try:
    #         from rich.console import Console
    #         console = Console(stderr=True)
    #         console.print("[bold red]Error:[/bold red] Running ADscan from a [bold yellow]pipx[/bold yellow] environment is not supported.")
    #         console.print("This tool requires direct system-level access. Please uninstall the pipx version ('pipx uninstall adscan') and install it globally:")
    #         console.print("  [cyan]sudo pip install adscan[/cyan]")
    #     except ImportError:
    #         print("Error: Running ADscan from a pipx environment is not supported.", file=sys.stderr)
    #         print("Please use 'sudo pip install adscan' instead.", file=sys.stderr)
    #     sys.exit(1)
    # # --- END PIPX EXECUTION BLOCK ---

    """
    This is the entry point for the 'adscan' command.
    It locates the bundled PyInstaller executable and runs it.
    """
    # Best-effort: remove the legacy alias that forced `sudo -E adscan` for all commands.
    # ADscan now escalates only when needed (e.g., install and specific system operations).
    _cleanup_legacy_sudo_alias()

    # Continue normal execution
    executable_path_str = ""
    try:
        # 'files('adscan_wrapper')' returns a path-like object to our package directory.
        # The 'adscan_bundle' is included as package_data, so it's inside this directory.
        executable_path = files('adscan_wrapper') / 'adscan_bundle' / 'adscan'
        executable_path_str = str(executable_path) # For error message

        # On some systems, the executable permission might be lost. Let's ensure it's set.
        if sys.platform != 'win32' and not os.access(executable_path, os.X_OK):
            os.chmod(executable_path, 0o755)

        # Use execv to replace the current python process with the adscan process.
        # This is efficient and correctly passes signals.
        args = [executable_path_str] + sys.argv[1:]
        os.execv(executable_path_str, args)

    except FileNotFoundError:
        print("ADScan Launcher Error: The executable was not found at the expected path:", file=sys.stderr)
        # Ensure executable_path_str has a value even if files() failed early
        if not executable_path_str:
            # Try to construct what it would have been for the error message
            try:
                executable_path_str = str(files('adscan_wrapper') / 'adscan_bundle' / 'adscan')
            except Exception:
                executable_path_str = "adscan_wrapper/adscan_bundle/adscan (path construction failed)"
        print(f"Expected: {executable_path_str}", file=sys.stderr)
        print("This may be due to an installation problem or the adscan_bundle not being correctly packaged.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("ADScan Launcher Error: An unexpected error occurred.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        if executable_path_str:
            print(f"Attempted to execute: {executable_path_str}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
