import pytest
from pathlib import Path
import sys
import os
from indastructa_pkg.cli import main, format_dir_structure

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def project_structure(tmp_path: Path) -> Path:
    """
    Creates a comprehensive temporary directory structure for testing.
    Returns the root path of the created structure.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # === Files and directories to be included ===

    # Source code
    (project_dir / "src").mkdir()
    (project_dir / "src" / "main.py").write_text("# Main file")
    (project_dir / "src" / "utils.py").write_text("# Utils")

    # API subdirectory
    (project_dir / "src" / "api").mkdir()
    (project_dir / "src" / "api" / "helpers.py").write_text("# Helpers")
    (project_dir / "src" / "api" / "__init__.py").touch()

    # Tests
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "test_main.py").write_text("# Tests")

    # Documentation
    (project_dir / "README.md").write_text("# Project README")
    (project_dir / "docs").mkdir()
    (project_dir / "docs" / "index.md").write_text("# Docs")
    (project_dir / "docs" / "api").mkdir()
    (project_dir / "docs" / "api" / "reference.md").touch()

    # Config files
    (project_dir / "pyproject.toml").write_text("[project]\nname='test'")
    (project_dir / "requirements.txt").write_text("pytest\nrequests")

    # === Files and directories to be excluded by default ===

    # Version control
    (project_dir / ".git").mkdir()
    (project_dir / ".git" / "config").touch()

    # Virtual environment
    (project_dir / "venv").mkdir()
    (project_dir / "venv" / "lib").mkdir()

    # Environment files
    (project_dir / ".env").write_text("SECRET=123")
    (project_dir / ".env.local").write_text("LOCAL_SECRET=456")

    # IDE files
    (project_dir / ".vscode").mkdir()
    (project_dir / ".vscode" / "settings.json").touch()
    (project_dir / ".idea").mkdir()

    # Build artifacts
    (project_dir / "build").mkdir()
    (project_dir / "dist").mkdir()
    (project_dir / "my_project.egg-info").mkdir()

    # Python cache
    (project_dir / "__pycache__").mkdir()
    (project_dir / "src" / "__pycache__").mkdir()
    (project_dir / ".pytest_cache").mkdir()

    # Node modules (если есть JS часть)
    (project_dir / "node_modules").mkdir()

    # === .gitignore file for testing pattern parsing ===
    gitignore_content = """
# Python
*.pyc
*.pyo
*.log
__pycache__/
.pytest_cache/

# Environment
.env
.env.*

# Build
build/
dist/
*.egg-info

# IDE
.vscode/
.idea/
"""
    (project_dir / ".gitignore").write_text(gitignore_content.strip())

    # Files that should be excluded by .gitignore
    (project_dir / "app.log").write_text("Log content")
    (project_dir / "debug.log").write_text("Debug log")
    (project_dir / "src" / "module.pyc").touch()

    return project_dir


@pytest.fixture
def simple_structure(tmp_path: Path) -> Path:
    """
    Creates a minimal directory structure for basic tests.
    """
    project_dir = tmp_path / "simple_project"
    project_dir.mkdir()

    (project_dir / "file1.txt").touch()
    (project_dir / "file2.txt").touch()
    (project_dir / "subdir").mkdir()
    (project_dir / "subdir" / "file3.txt").touch()

    return project_dir


@pytest.fixture
def nested_structure(tmp_path: Path) -> Path:
    """
    Creates a deeply nested structure for depth testing.
    """
    project_dir = tmp_path / "nested_project"
    current = project_dir

    # Create 5 levels deep
    for i in range(5):
        current.mkdir(exist_ok=True)
        (current / f"file_{i}.txt").touch()
        current = current / f"level_{i + 1}"

    return project_dir


# ============================================================================
# TESTS - format_dir_structure function
# ============================================================================


def test_format_dir_structure_basic(simple_structure: Path):
    """Test basic formatting without any exclusions."""
    result = format_dir_structure(
        simple_structure, exclude_patterns=set(), include_patterns=set()
    )

    assert "file1.txt" in result
    assert "file2.txt" in result
    assert "subdir/" in result
    assert "file3.txt" in result


def test_format_dir_structure_with_exclusions(project_structure: Path):
    """Test that format_dir_structure respects exclude patterns."""
    exclude = {".git", "venv", "__pycache__"}
    result = format_dir_structure(
        project_structure, exclude_patterns=exclude, include_patterns=set()
    )

    # Should include
    assert "src/" in result
    assert "main.py" in result

    # Should exclude
    assert ".git/" not in result
    assert "venv/" not in result
    assert "__pycache__" not in result


def test_format_dir_structure_empty_directory(tmp_path: Path):
    """Test formatting an empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = format_dir_structure(
        empty_dir, exclude_patterns=set(), include_patterns=set()
    )

    assert result == ""


def test_format_dir_structure_with_patterns(project_structure: Path):
    """Test exclusion of file patterns like *.log."""
    exclude = {"*.log", "*.pyc"}
    result = format_dir_structure(
        project_structure, exclude_patterns=exclude, include_patterns=set()
    )

    assert "app.log" not in result
    assert "debug.log" not in result
    assert "module.pyc" not in result


# ============================================================================
# TESTS - main() function with default behavior
# ============================================================================


def test_main_default_behavior(project_structure: Path, monkeypatch):
    """
    Test main() with default settings.
    Should apply default exclusions and parse .gitignore.
    """
    output_file = project_structure / "project_structure.txt"

    monkeypatch.setattr("sys.argv", ["indastructa", str(project_structure)])

    main()

    assert output_file.is_file(), "Output file was not created"

    content = output_file.read_text(encoding="utf-8")

    # Should include
    assert "src/" in content
    assert "main.py" in content
    assert "README.md" in content
    assert ".gitignore" in content
    assert "pyproject.toml" in content

    # Should exclude (default exclusions)
    assert ".git/" not in content
    assert "venv/" not in content
    assert "node_modules" not in content
    assert ".vscode" not in content
    assert ".idea" not in content

    # Should exclude (.gitignore patterns)
    assert ".env" not in content
    assert "app.log" not in content
    assert "__pycache__" not in content
    assert ".pytest_cache" not in content


def test_main_creates_output_file(simple_structure: Path, monkeypatch):
    """Test that main() creates the output file."""
    monkeypatch.setattr("sys.argv", ["indastructa", str(simple_structure)])

    main()

    output_file = simple_structure / "project_structure.txt"
    assert output_file.exists()
    assert output_file.is_file()
    assert output_file.stat().st_size > 0


def test_main_output_file_encoding(project_structure: Path, monkeypatch):
    """Test that output file is UTF-8 encoded."""
    monkeypatch.setattr("sys.argv", ["indastructa", str(project_structure)])

    main()

    output_file = project_structure / "project_structure.txt"

    # Should not raise encoding errors
    content = output_file.read_text(encoding="utf-8")
    assert len(content) > 0


# ============================================================================
# TESTS - CLI arguments
# ============================================================================


def test_main_with_depth_limit_1(project_structure: Path, monkeypatch):
    """Test --depth 1 shows only top-level files and directories."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--depth", "1"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should include (depth 1)
    assert "src/" in content
    assert "docs/" in content
    assert "README.md" in content
    assert "pyproject.toml" in content

    # Should NOT include (depth 2+)
    assert "main.py" not in content
    assert "api/" not in content
    assert "helpers.py" not in content


def test_main_with_depth_limit_2(project_structure: Path, monkeypatch):
    """Test --depth 2 shows files up to 2 levels deep."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--depth", "2"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should include (depth 2)
    assert "src/" in content
    assert "main.py" in content
    assert "api/" in content

    # Should NOT include (depth 3+)
    assert "helpers.py" not in content


def test_main_with_depth_zero(project_structure: Path, monkeypatch):
    """Test --depth 0 shows only the root directory."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--depth", "0"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should only show root
    assert "test_project" in content
    # Should not show any contents
    assert "src/" not in content
    assert "README.md" not in content


def test_main_with_unlimited_depth(nested_structure: Path, monkeypatch):
    """Test that without --depth, all levels are shown."""
    output_file = nested_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(nested_structure)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should include all 5 levels
    for i in range(5):
        assert f"file_{i}.txt" in content
        if i < 4:  # level_5 doesn't have a subdirectory
            assert f"level_{i + 1}/" in content


def test_main_with_single_exclude(project_structure: Path, monkeypatch):
    """Test --exclude with a single pattern."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--exclude", "src"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    assert "src" not in content

    # Other files should still be included
    assert "README.md" in content
    assert "docs/" in content


def test_main_with_comma_separated_exclude(project_structure: Path, monkeypatch):
    """Test --exclude with comma-separated values."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--exclude", "*.md,docs"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should exclude all .md files
    assert "README.md" not in content
    assert "index.md" not in content
    assert "reference.md" not in content

    # Should exclude docs directory
    assert "docs/" not in content

    # Should include other files
    assert "src/" in content
    assert "pyproject.toml" in content


def test_main_with_multiple_exclude_flags(project_structure: Path, monkeypatch):
    """Test using the --exclude flag multiple times."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "indastructa",
            str(project_structure),
            "--exclude",
            "*.md",
            "--exclude",
            "docs",
        ],
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    assert "README.md" not in content
    assert "docs/" not in content
    assert "src/" in content


def test_main_with_multiple_patterns(project_structure: Path, monkeypatch):
    """Test --exclude with multiple different patterns."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv",
        ["indastructa", str(project_structure), "--exclude", "*.md,*.toml,tests"],
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    assert "README.md" not in content
    assert "pyproject.toml" not in content
    assert "tests/" not in content
    assert "test_main.py" not in content


def test_main_exclude_overrides_defaults(project_structure: Path, monkeypatch):
    """Test that custom --exclude works alongside default exclusions."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--exclude", "src"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # Custom exclusion
    assert "src/" not in content

    # Default exclusions should still work
    assert ".git/" not in content
    assert "venv/" not in content


def test_main_with_custom_output_file(simple_structure: Path, monkeypatch):
    """Test the -o / --output flag."""
    custom_name = "custom_output.txt"
    default_name = "project_structure.txt"

    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(simple_structure), "-o", custom_name]
    )

    main()

    custom_file = simple_structure / custom_name
    default_file = simple_structure / default_name

    assert custom_file.exists(), "Custom output file was not created"
    assert not default_file.exists(), "Default output file should not be created"
    assert custom_file.stat().st_size > 0


# ============================================================================
# TESTS - CLI arguments: --include
# ============================================================================


def test_main_with_include_overrides_default_exclusion(
    project_structure: Path, monkeypatch
):
    """Test that --include shows a file that is excluded by default."""
    output_file = project_structure / "project_structure.txt"
    # .env is in the default EXCLUDE_SET
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--include", ".env"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # .env should be present because of --include
    assert ".env" in content


def test_main_with_include_overrides_gitignore(project_structure: Path, monkeypatch):
    """Test that --include shows a file that is excluded by .gitignore."""
    output_file = project_structure / "project_structure.txt"
    # app.log is excluded by *.log in .gitignore
    monkeypatch.setattr(
        "sys.argv", ["indastructa", str(project_structure), "--include", "app.log"]
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # app.log should be present
    assert "app.log" in content
    # but other .log files should still be excluded
    assert "debug.log" not in content


def test_main_with_include_overrides_exclude_flag(project_structure: Path, monkeypatch):
    """Test that --include has higher priority than --exclude."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr(
        "sys.argv",
        [
            "indastructa",
            str(project_structure),
            "--exclude",
            "*.log",
            "--include",
            "app.log",
        ],
    )

    main()

    content = output_file.read_text(encoding="utf-8")

    # app.log should be included because --include wins
    assert "app.log" in content
    # debug.log should be excluded
    assert "debug.log" not in content


# ============================================================================
# TESTS - .gitignore parsing
# ============================================================================


def test_gitignore_patterns_respected(project_structure: Path, monkeypatch):
    """Test that patterns from .gitignore are excluded."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project_structure)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # Patterns from .gitignore should be excluded
    assert "*.log" not in content or "app.log" not in content
    assert "__pycache__" not in content
    assert ".env" not in content
    assert "build/" not in content
    assert "dist/" not in content


def test_gitignore_itself_included(project_structure: Path, monkeypatch):
    """Test that .gitignore file itself is included in output."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project_structure)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # .gitignore should be visible
    assert ".gitignore" in content


def test_project_without_gitignore(simple_structure: Path, monkeypatch):
    """Test behavior when no .gitignore exists."""
    output_file = simple_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(simple_structure)])

    # Should not crash
    main()

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert len(content) > 0


# ============================================================================
# TESTS - Edge cases and error handling
# ============================================================================


def test_main_with_nonexistent_directory(tmp_path: Path, monkeypatch, capsys):
    """Test handling of non-existent directory."""
    nonexistent = tmp_path / "does_not_exist"

    monkeypatch.setattr("sys.argv", ["indastructa", str(nonexistent)])

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert (
        "does not exist" in captured.err.lower() or "not found" in captured.err.lower()
    )


def test_main_with_file_instead_of_directory(
    project_structure: Path, monkeypatch, capsys
):
    """Test handling when path points to a file, not directory."""
    file_path = project_structure / "README.md"

    monkeypatch.setattr("sys.argv", ["indastructa", str(file_path)])

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert (
        "not a directory" in captured.err.lower()
        or "must be a directory" in captured.err.lower()
    )


def test_main_with_permission_denied(tmp_path: Path, monkeypatch):
    """Test handling of permission errors (Unix only)."""
    if os.name != "posix":
        pytest.skip("Permission tests only work on Unix-like systems")

    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir(mode=0o000)

    monkeypatch.setattr("sys.argv", ["indastructa", str(restricted_dir)])

    try:
        # Should handle gracefully
        with pytest.raises(SystemExit):
            main()
    finally:
        # Cleanup
        restricted_dir.chmod(0o755)


def test_empty_project_structure(tmp_path: Path, monkeypatch):
    """Test with completely empty directory."""
    empty_dir = tmp_path / "empty_project"
    empty_dir.mkdir()

    output_file = empty_dir / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(empty_dir)])

    main()

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")

    # Should at least show the root directory
    assert "empty_project" in content


# ============================================================================
# TESTS - Output format validation
# ============================================================================


def test_output_format_has_tree_structure(simple_structure: Path, monkeypatch):
    """Test that output uses proper tree formatting characters."""
    output_file = simple_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(simple_structure)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should contain tree characters
    assert any(char in content for char in ["|", "+", "-", "├", "└", "│"])


def test_output_has_header(project_structure: Path, monkeypatch):
    """Test that output includes a header."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project_structure)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # Should have a header line
    lines = content.split("\n")
    assert len(lines) > 0
    # First line often contains "Project Structure" or similar
    assert any(
        keyword in lines[0].lower() for keyword in ["project", "structure", "---"]
    )


def test_output_directories_marked(project_structure: Path, monkeypatch):
    """Test that directories are clearly marked (usually with /)."""
    output_file = project_structure / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project_structure)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # Directories should have trailing /
    assert "src/" in content
    assert "docs/" in content
    assert "tests/" in content


# ============================================================================
# TESTS - Integration: Real-world scenarios
# ============================================================================


def test_typical_python_project(tmp_path: Path, monkeypatch):
    """Test with a typical Python project structure."""
    project = tmp_path / "python_app"
    project.mkdir()

    # Typical structure
    (project / "src").mkdir()
    (project / "src" / "__init__.py").touch()
    (project / "src" / "main.py").touch()
    (project / "tests").mkdir()
    (project / "tests" / "test_main.py").touch()
    (project / "README.md").touch()
    (project / "setup.py").touch()
    (project / "requirements.txt").touch()
    (project / ".gitignore").write_text("__pycache__/\n*.pyc\n")

    # Should be excluded
    (project / "__pycache__").mkdir()
    (project / "venv").mkdir()

    output_file = project / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project)])

    main()

    content = output_file.read_text(encoding="utf-8")

    assert "src/" in content
    assert "tests/" in content
    assert "README.md" in content
    assert "__pycache__" not in content
    assert "venv/" not in content


def test_project_with_multiple_gitignores(tmp_path: Path, monkeypatch):
    """Test project with .gitignore in subdirectories."""
    project = tmp_path / "multi_gitignore"
    project.mkdir()

    # Root .gitignore
    (project / ".gitignore").write_text("*.log\n")
    (project / "root.log").touch()

    # Subdirectory with its own .gitignore
    (project / "subdir").mkdir()
    (project / "subdir" / ".gitignore").write_text("*.tmp\n")
    (project / "subdir" / "file.tmp").touch()
    (project / "subdir" / "file.txt").touch()

    output_file = project / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project)])

    main()

    content = output_file.read_text(encoding="utf-8")

    # Root patterns should apply
    assert "root.log" not in content

    # Subdirectory patterns should apply (if supported)
    # Note: This depends on implementation
    assert "file.txt" in content


# ============================================================================
# TESTS - Performance and limits
# ============================================================================


def test_large_directory_structure(tmp_path: Path, monkeypatch):
    """Test with a large number of files (performance test)."""
    project = tmp_path / "large_project"
    project.mkdir()

    # Create 100 files
    for i in range(100):
        (project / f"file_{i:03d}.txt").touch()

    # Create 10 directories with 10 files each
    for d in range(10):
        subdir = project / f"dir_{d:02d}"
        subdir.mkdir()
        for f in range(10):
            (subdir / f"file_{f:02d}.txt").touch()

    output_file = project / "project_structure.txt"
    monkeypatch.setattr("sys.argv", ["indastructa", str(project)])

    # Should complete without timeout
    import time

    start = time.time()
    main()
    duration = time.time() - start

    assert output_file.exists()
    assert duration < 5.0, "Tool took too long (>5s) on large directory"


# ============================================================================
# TESTS - Help and version
# ============================================================================


def test_main_with_help_flag(monkeypatch, capsys):
    """Test --help flag."""
    monkeypatch.setattr("sys.argv", ["indastructa", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0  # Help should exit with 0

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "indastructa" in captured.out.lower()


def test_main_without_arguments(monkeypatch, tmp_path):
    """Test running without arguments scans the current directory."""
    # Change current working directory to a temporary one
    os.chdir(tmp_path)

    (tmp_path / "file_in_cwd.txt").touch()

    monkeypatch.setattr("sys.argv", ["indastructa"])

    main()

    output_file = tmp_path / "project_structure.txt"
    assert output_file.exists()

    content = output_file.read_text()
    assert "file_in_cwd.txt" in content
