import os
import subprocess
import webbrowser
from pathlib import Path

from pygeai.cli.commands import Command, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import DOCS_HELP_TEXT
from pygeai.core.utils.console import Console


def show_help():
    help_text = build_help_text(docs_commands, DOCS_HELP_TEXT)
    Console.write_stdout(help_text)


def open_documentation():
    try:
        import sphinx
    except ImportError:
        Console.write_stdout(
            "Documentation dependencies (sphinx, sphinx-rtd-theme) are not installed.\n"
            "Would you like to install them now? [Y/n]: "
        )
        response = input().strip().lower()
        
        if response in ['', 'y', 'yes']:
            Console.write_stdout("Installing documentation dependencies...")
            try:
                subprocess.run(
                    ["pip", "install", "pygeai[docs]"],
                    check=True,
                    text=True
                )
                Console.write_stdout("Documentation dependencies installed successfully.")
            except subprocess.CalledProcessError as e:
                Console.write_stderr(f"ERROR: Failed to install dependencies.\n{e}")
                return
            except FileNotFoundError:
                Console.write_stderr("ERROR: pip command not found.")
                return
        else:
            Console.write_stdout("Installation cancelled. Documentation dependencies are required.")
            return

    pygeai_package_dir = Path(__file__).parent.parent.parent
    docs_dir = pygeai_package_dir / "_docs"
    build_dir = docs_dir / "build" / "html"
    index_file = build_dir / "index.html"

    if not index_file.exists():
        Console.write_stdout("Documentation not found. Building documentation (this may take a minute)...")
        source_dir = docs_dir / "source"
        
        try:
            result = subprocess.run(
                ["sphinx-build", "-b", "html", str(source_dir), str(build_dir)],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            Console.write_stdout("Documentation built successfully.")
        except subprocess.CalledProcessError as e:
            Console.write_stderr(f"ERROR: Failed to build documentation.\n{e.stderr}")
            return
        except subprocess.TimeoutExpired:
            Console.write_stderr("ERROR: Documentation build timed out after 5 minutes.")
            return
        except FileNotFoundError:
            Console.write_stderr(
                "ERROR: sphinx-build command not found.\n"
                "Install documentation dependencies: pip install pygeai[docs]"
            )
            return

    doc_url = f"file://{index_file.absolute()}"
    Console.write_stdout(f"Opening documentation at: {doc_url}")
    
    try:
        webbrowser.open(doc_url)
    except Exception as e:
        Console.write_stderr(f"ERROR: Failed to open browser.\n{e}")


docs_commands = [
    Command(
        "open",
        ["open", "o"],
        "Open documentation in web browser",
        open_documentation,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
]
