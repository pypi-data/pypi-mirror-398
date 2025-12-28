import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from importlib import resources


def get_man_dir() -> Path | None:
    """Locate the pygeai/man/man1 directory within the installed package."""
    try:
        # Use importlib.resources to find the man/man1 directory in pygeai package
        with resources.path("pygeai.man", "man1") as man_path:
            man_dir = Path(man_path)
            if man_dir.is_dir():
                return man_dir
        return None
    except (ImportError, FileNotFoundError):
        return None


def validate_man_file(file_path: Path) -> bool:
    """Validate if a file is a likely man page (ends with .1 or .1.gz)."""
    return file_path.suffix in ('.1', '.gz') and (file_path.name.endswith('.1') or file_path.name.endswith('.1.gz'))


def install_man_pages(system_wide: bool) -> int:
    """Install man pages from pygeai/man/man1 to local or system-wide man directory."""
    # Locate source directory
    source_path = get_man_dir()
    if not source_path:
        print("Error: Could not locate 'pygeai/man/man1' directory in the installed pygeai package.")
        return 1

    # Determine destination directory
    if system_wide:
        dest_path = Path("/usr/local/share/man/man1")
    else:
        dest_path = Path.home() / "share" / "man" / "man1"

    # Ensure destination directory exists
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Error: Permission denied creating '{dest_path}'. Try running with sudo for system-wide installation.")
        return 1

    # Collect man page files
    man_files = [f for f in source_path.iterdir() if validate_man_file(f)]
    if not man_files:
        print(f"Warning: No valid man page files found in '{source_path}'.")
        return 0

    # Copy man page files
    for man_file in man_files:
        dest_file = dest_path / man_file.name
        try:
            shutil.copy2(man_file, dest_file)
            print(f"Installed: {dest_file}")
            # Set permissions (644)
            dest_file.chmod(0o644)
        except PermissionError:
            print(f"Error: Permission denied copying '{man_file}' to '{dest_file}'. Try running with sudo.")
            return 1
        except OSError as e:
            print(f"Error: Failed to copy '{man_file}' to '{dest_file}': {e}")
            return 1

    # Update man database for system-wide installation
    if system_wide:
        try:
            subprocess.run(["mandb"], check=True, capture_output=True, text=True)
            print("Updated man page database.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to update man database: {e.stderr}")
        except FileNotFoundError:
            print("Warning: 'mandb' command not found. Man pages installed but database not updated.")

    # For local installation, remind user to update MANPATH
    if not system_wide:
        manpath_cmd = f'export MANPATH={Path.home() / "share" / "man"}:$MANPATH'
        print(f"Local installation complete. Add to ~/.bashrc to update MANPATH:")
        print(f"    {manpath_cmd}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Install man pages from pygeai/man/man1.")
    parser.add_argument(
        "--system",
        action="store_true",
        help="Install man pages system-wide to /usr/local/share/man/man1 (requires sudo).",
    )
    args = parser.parse_args()

    # Check if running as root for system-wide installation
    if args.system and os.geteuid() != 0:
        print("Error: System-wide installation requires root privileges. Run with sudo.")
        sys.exit(1)

    sys.exit(install_man_pages(args.system))


if __name__ == "__main__":
    main()