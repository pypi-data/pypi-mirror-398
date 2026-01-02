import argparse
import fnmatch
from pathlib import Path
import textwrap
from typing import Set, List
import sys

# --- Global Constants ---
PROJECT_DIR: Path = Path.cwd()
OUTPUT_FILENAME: Path = Path("project_structure.txt")

# Base set of files and directories to ignore.
EXCLUDE_SET: Set[str] = {
    ".git",
    ".idea",
    ".vscode",
    ".history",
    "logs",
    ".DS_Store",
    "__pycache__",
    ".ruff_cache",
    ".venv",
    "venv",
    "Scripts",
    "*.pyc",
    "*.egg-info",
    "node_modules",
    "dist",
    "build",
    ".next",
    "migrations",
    "migrations.py",
    "migrations_old",
    ".env",
    ".idea_modules",
    "atlassian-ide-plugin.xml",
}


def get_patterns_from_ignore_files(
    directory: Path, ignore_filenames: List[str]
) -> Set[str]:
    """
    Reads multiple ignore files (e.g., .gitignore, .dockerignore) from a directory
    and returns a combined set of unique patterns.
    """
    all_patterns: Set[str] = set()
    for filename in ignore_filenames:
        ignore_file_path = directory / filename
        try:
            if ignore_file_path.is_file():
                with ignore_file_path.open("r", encoding="utf-8") as f:
                    patterns = {
                        line.strip()
                        for line in f
                        if line.strip() and not line.strip().startswith("#")
                    }
                    all_patterns.update(patterns)
        except (IOError, PermissionError):
            continue
    return all_patterns


def is_excluded(
    path: Path, exclude_patterns: Set[str], include_patterns: Set[str]
) -> bool:
    """
    Checks if a given path should be excluded based on include and exclude patterns.
    Include patterns have higher priority.
    """
    # If the path matches an include pattern, it should NOT be excluded.
    for pattern in include_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return False

    # If not included, check if it matches an exclude pattern.
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True

    return False


def format_dir_structure(
    root_path: Path,
    exclude_patterns: Set[str],
    include_patterns: Set[str],
    prefix: str = "",
    max_depth: int = -1,
    current_depth: int = 0,
) -> str:
    """
    Recursively builds a string representation of a directory structure.
    """
    if max_depth != -1 and current_depth >= max_depth:
        return ""

    try:
        all_path_items = root_path.iterdir()
        filtered_items = [
            path
            for path in all_path_items
            if not is_excluded(path, exclude_patterns, include_patterns)
        ]
        sorted_items = sorted(
            filtered_items, key=lambda p: (p.is_file(), p.name.lower())
        )
    except (FileNotFoundError, PermissionError):
        return ""

    parts = []
    for i, item in enumerate(sorted_items):
        is_last = i == len(sorted_items) - 1
        connector = "  +-- " if is_last else "  |-- "
        item_display_name = f"{item.name}{'/' if item.is_dir() else ''}"
        parts.append(f"{prefix}{connector}{item_display_name}")

        if item.is_dir():
            new_prefix = prefix + ("      " if is_last else "  |   ")
            parts.append(
                format_dir_structure(
                    item,
                    exclude_patterns,
                    include_patterns,
                    new_prefix,
                    max_depth,
                    current_depth + 1,
                )
            )
    return "\n".join(parts)


def write_structure_to_file(output_file: Path, content: str) -> None:
    """Writes the directory structure to a file."""
    try:
        output_file.write_text(content, encoding="utf-8")
        print(f"Project structure successfully saved to: {output_file}")
    except IOError as e:
        print(f"Error writing to file {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """The main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate ASCII tree representation of a project structure.",
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              # 1. Scan the current directory
              indastructa

              # 2. Scan a specific directory
              indastructa ./src

              # 3. Scan with a depth limit and save to a different file
              indastructa --depth 2 -o custom_name.txt

              # 4. Exclude multiple patterns (use quotes for safety)
              indastructa --exclude "*.log,node_modules"

              # 5. Force include a file that is normally excluded (e.g., by .gitignore)
              indastructa --include .env

              # 6. Perform a dry run without writing to a file
              indastructa --dry-run

              # 7. A complex example
              indastructa ./src --depth 3 --exclude "*.pyc" --include ".env" -o structure.md
        """),
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="The path to the directory to scan. Defaults to the current directory.",
    )
    parser.add_argument("--depth", type=int, default=-1, help="Maximum depth to scan.")
    parser.add_argument(
        "--exclude",
        action="append",
        nargs="*",
        default=[],
        help="Additional files or directories to exclude, separated by commas.",
    )
    parser.add_argument(
        "--include",
        action="append",
        nargs="*",
        default=[],
        help="Files or directories to force include, even if they are in .gitignore.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(OUTPUT_FILENAME.name),
        help="Name of the output file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a trial run without writing the output file.",
    )

    args = parser.parse_args()

    if args.path is None:
        project_dir = Path.cwd()
    else:
        project_dir = Path(args.path).resolve()

    if not project_dir.exists():
        print(f"Error: Provided path does not exist: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if not project_dir.is_dir():
        print(f"Error: Path is not a directory: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # --- Assemble all exclusion and inclusion patterns ---
    final_exclude_patterns = EXCLUDE_SET.copy()
    final_include_patterns = set()

    ignore_files = [".gitignore", ".dockerignore"]
    ignore_patterns = get_patterns_from_ignore_files(project_dir, ignore_files)
    final_exclude_patterns.update(p.strip("/") for p in ignore_patterns)

    # Flatten the list of lists that argparse creates with action='append'
    flat_excludes = [item for sublist in args.exclude for item in sublist]
    if flat_excludes:
        exclude_list = [
            item.strip() for arg in flat_excludes for item in arg.split(",")
        ]
        final_exclude_patterns.update(exclude_list)

    flat_includes = [item for sublist in args.include for item in sublist]
    if flat_includes:
        include_list = [
            item.strip() for arg in flat_includes for item in arg.split(",")
        ]
        final_include_patterns.update(include_list)

    final_exclude_patterns.add(args.output)
    final_exclude_patterns.add(Path(__file__).name)

    # --- Generation and Writing ---
    structure_text = format_dir_structure(
        project_dir,
        final_exclude_patterns,
        final_include_patterns,
        max_depth=args.depth,
    )

    output_content = f"{project_dir.name}/\n{structure_text}\n"

    if args.dry_run:
        print("-- DRY RUN MODE --")
        print("The following structure would be generated, but not saved to a file:")
    else:
        output_filename = project_dir / args.output
        write_structure_to_file(output_filename, output_content)

    print("\n--- Project Structure ---")
    print(output_content)


if __name__ == "__main__":
    main()
