# Indastructa

**Indastructa** is a convenient CLI tool for quickly creating a clear ASCII tree of your project's file structure.

Perfect for documentation, technical reviews, architecture discussions, or blog posts.

---

## Key Features

* **Clear Output:** Generates a beautiful and easy-to-read ASCII tree.
* **Automatic Saving:** The result is automatically saved to a `project_structure.txt` file in the project root.
* **Smart Exclusions:** By default, it ignores unnecessary files and folders (such as `.git`, `venv`, `__pycache__`, `.idea`, and others).
* **Integration with `.gitignore`:** Automatically reads rules from `.gitignore` and `.dockerignore` to exclude everything unrelated to source code.
* **Flexible Configuration:** Allows specifying target folder, limiting scan depth, and adding custom exclusions and inclusions via command-line arguments.

---

## Installation

You can install `indastructa` from PyPI or TestPyPI.

**Stable Version (from PyPI)**

This is the recommended way to install the latest stable release.

```bash
pip install indastructa
```

**Development Version (from TestPyPI)**

To install the latest pre-release version from our test repository:

```bash
pip install --index-url https://test.pypi.org/simple/ indastructa
```

---

## How to Use

### Basic Usage

To scan the current directory, simply run the command:

```bash
indastructa
```

The result will be printed to the console and saved to `project_structure.txt`.

### Specifying a Path

You can scan any directory by providing a relative or absolute path:

```bash
# Scan a subdirectory
indastructa ./src

# Scan a directory using an absolute path
indastructa C:\Users\YourUser\Projects\MyProject
```

---

## Advanced Usage

You can combine flags to customize the output.

*   **Limit scan depth** with `--depth`:

    ```bash
    indastructa --depth 2
    ```

*   **Exclude files and folders** with `--exclude` (use quotes for multiple patterns):

    ```bash
    indastructa --exclude "*.md,docs,build"
    ```

*   **Force include files** with `--include` to show them even if they are in `.gitignore`:

    ```bash
    indastructa --include .env
    ```

*   **Save to a different file** with `-o` or `--output`:

    ```bash
    indastructa -o custom_structure.md
    ```

*   **Perform a dry run** with `--dry-run` to see the output without saving the file:

    ```bash
    indastructa --dry-run
    ```

### Full Example

Here is a complex example combining all options:

```bash
indastructa ./src --depth 3 --exclude "*.pyc" --include ".env" -o src_structure.txt
```

---

## Exclusion Logic

`indastructa` uses a filtering system with the following priority:

1. **`--include` rules:** Patterns passed via `--include` have the highest priority. If a file matches, it will always be shown.
2. **Built-in rules:** A default set of common exclusions like `.git`, `venv`, `__pycache__`, etc.
3. **Rules from `.gitignore` and `.dockerignore`:** Automatically loaded from your project.
4. **`--exclude` rules:** Patterns passed via `--exclude`.

---

## Future Ideas

For more advanced feature ideas, see the `FUTURE_FEATURES.md` file in this repository.

- Selectable ignore files
- Interactive mode
- Support for exporting to JSON/YAML

Have ideas or found a bug? Create an Issue on GitHub.

---

## License

The project is distributed under the MIT License.
