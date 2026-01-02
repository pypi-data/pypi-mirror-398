"""Command-line interface for code-typer."""

import sys
from pathlib import Path
from typing import Optional

import click

from code_typer import __version__


@click.command()
@click.argument("path", type=click.Path(), required=False, default=None)
@click.option(
    "--speed",
    "-s",
    type=float,
    default=1.0,
    help="Typing speed multiplier (1.0 = normal, 2.0 = twice as fast)",
)
@click.option(
    "--error-rate",
    "-e",
    type=float,
    default=0.06,
    help="Probability of making errors (0.0-1.0, default 0.06)",
)
@click.option(
    "--no-highlight",
    is_flag=True,
    help="Disable syntax highlighting",
)
@click.option(
    "--pause-between-files",
    type=float,
    default=1.0,
    help="Pause duration in seconds between files when showcasing a directory",
)
@click.option(
    "--smart/--no-smart",
    default=None,
    help="Use smart Python simulation (auto-enabled for .py files, use --no-smart to disable)",
)
@click.option(
    "--language",
    "-l",
    type=click.Choice(["python", "sql", "text"], case_sensitive=False),
    default="python",
    help="Language for syntax highlighting when reading from stdin (default: python)",
)
@click.version_option(version=__version__)
def main(
    path: Optional[str],
    speed: float,
    error_rate: float,
    no_highlight: bool,
    pause_between_files: float,
    smart: Optional[bool],
    language: str,
) -> None:
    """Showcase code files with human-like typing simulation.

    PATH can be a single file, a directory, or '-' for stdin.
    If no PATH is given and stdin is piped, reads from stdin.

    Examples:

        showcase example.py

        showcase ./src --speed 1.5 --error-rate 0.05

        cat script.py | showcase --smart --speed 5

        showcase - --language sql < query.sql
    """
    from code_typer.display import NcursesDisplay
    from code_typer.file_handler import FileHandler, FileInfo
    from code_typer.typer_engine import TyperEngine

    # Determine if we're reading from stdin
    read_from_stdin = False
    stdin_content = None

    if path == "-":
        read_from_stdin = True
    elif path is None:
        # No path given - check if stdin has data (is piped)
        if not sys.stdin.isatty():
            read_from_stdin = True
        else:
            click.echo(
                "Error: No input provided. Specify a PATH or pipe content via stdin.",
                err=True,
            )
            click.echo("Usage: showcase FILE or cat FILE | showcase --smart", err=True)
            sys.exit(1)

    # Read stdin content BEFORE starting ncurses (stdin won't be available after)
    if read_from_stdin:
        stdin_content = sys.stdin.read()
        if not stdin_content.strip():
            click.echo("Error: No content received from stdin.", err=True)
            sys.exit(1)

    verification_results: list[
        tuple[str, bool, str]
    ] = []  # (filename, success, message)

    try:
        with NcursesDisplay() as display:
            engine = TyperEngine(
                display=display,
                speed=speed,
                error_rate=error_rate,
                enable_highlight=not no_highlight,
            )

            if read_from_stdin:
                # Create a FileInfo-like object for stdin content
                # stdin_content is guaranteed non-None here due to check above
                assert stdin_content is not None
                file_info = FileInfo(
                    path=Path("<stdin>"),
                    content=stdin_content,
                    language=language.lower(),
                )

                display.show_file_header(file_info.path, len(file_info.content))

                # Auto-enable smart mode for Python (unless explicitly disabled)
                use_smart = (
                    smart if smart is not None else (file_info.language == "python")
                )
                if use_smart and file_info.language == "python":
                    from code_typer.realistic_python_typer import content_hash

                    source_hash = content_hash(stdin_content)
                    verified = engine.type_python_smart(
                        file_info.content, skeleton_first=True
                    )
                    if verified:
                        verification_results.append(("<stdin>", True, source_hash[:16]))
                    else:
                        verification_results.append(
                            (
                                "<stdin>",
                                False,
                                engine._verification_error or "Unknown error",
                            )
                        )
                else:
                    engine.type_content(file_info.content, file_info.language)
            else:
                # Read from file/directory
                assert path is not None  # Guaranteed by check above
                path_obj = Path(path)
                if not path_obj.exists():
                    click.echo(f"Error: Path '{path}' does not exist.", err=True)
                    sys.exit(1)

                file_handler = FileHandler(path_obj)

                for file_info in file_handler.iterate_files():
                    # Reset engine state for each new file to prevent fatigue/momentum accumulation
                    engine.reset()
                    display.show_file_header(file_info.path, len(file_info.content))

                    # Auto-enable smart mode for Python files (unless explicitly disabled)
                    use_smart = (
                        smart if smart is not None else (file_info.language == "python")
                    )
                    if use_smart and file_info.language == "python":
                        from code_typer.realistic_python_typer import content_hash

                        source_hash = content_hash(file_info.content)
                        verified = engine.type_python_smart(
                            file_info.content, skeleton_first=True
                        )
                        if verified:
                            verification_results.append(
                                (str(file_info.path), True, source_hash[:16])
                            )
                        else:
                            verification_results.append(
                                (
                                    str(file_info.path),
                                    False,
                                    engine._verification_error or "Unknown error",
                                )
                            )
                        # Note: engine.reset() at start of loop handles _verification_error
                    else:
                        engine.type_content(file_info.content, file_info.language)

                    if file_handler.has_more_files():
                        display.show_file_transition(pause_between_files)

            # Wait for user to review and press 'q' to exit
            # Allows scrolling with arrow keys, page up/down, g/G
            display.wait_for_exit()

    except KeyboardInterrupt:
        click.echo("\nShowcase interrupted.", err=True)
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Report verification results after ncurses exits
    if verification_results:
        # Reset terminal and ensure cursor is at a clean position
        # Move to new line, clear any partial content
        print("\033[0m", end="")  # Reset all attributes
        print()  # New line to ensure clean start

        failed = [r for r in verification_results if not r[1]]
        passed = [r for r in verification_results if r[1]]

        if passed:
            print("SHA256 Verification:")
            for filename, _, hash_prefix in passed:
                print(f"  ✓ {filename} [{hash_prefix}...]")

        if failed:
            print("\nSHA256 VERIFICATION FAILED:", file=sys.stderr)
            for filename, _, error in failed:
                print(f"\n  File: {filename}", file=sys.stderr)
                for line in error.split("\n"):
                    print(f"    {line}", file=sys.stderr)
            sys.exit(2)  # Exit with error code 2 for verification failure


if __name__ == "__main__":
    main()
