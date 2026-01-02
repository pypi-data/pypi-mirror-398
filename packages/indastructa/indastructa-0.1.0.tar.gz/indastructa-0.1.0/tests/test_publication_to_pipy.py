import os
import requests
import toml
from pathlib import Path
import pytest

# Define the project root relative to this file's location
PROJECT_ROOT = Path(__file__).parent.parent

# --- Configuration for different repositories ---
REPOSITORIES = {
    "testpypi": {
        "url_template": "https://test.pypi.org/pypi/{package_name}/{version}/json",
        "name": "TestPyPI",
    },
    "pypi": {
        "url_template": "https://pypi.org/pypi/{package_name}/{version}/json",
        "name": "PyPI",
    },
}

# Determine which repository to check based on an environment variable
# Defaults to 'testpypi' if the variable is not set.
TARGET_REPO = os.environ.get("PYPI_TARGET", "testpypi")
if TARGET_REPO not in REPOSITORIES:
    pytest.fail(
        f"Invalid PYPI_TARGET: '{TARGET_REPO}'. Must be one of {list(REPOSITORIES.keys())}"
    )

PYPI_CONFIG = REPOSITORIES[TARGET_REPO]


@pytest.mark.network
def test_version_is_not_published():
    """
    Checks that the current version in pyproject.toml does not yet exist on the target repository.
    """
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "'pyproject.toml' not found at project root"

    # 1. Read package name and version from pyproject.toml
    config = toml.load(pyproject_path)
    package_name = config["project"]["name"]
    current_version = config["project"]["version"]

    assert package_name, "Package name is not defined in 'pyproject.toml'"
    assert current_version, "Version is not defined in 'pyproject.toml'"

    # 2. Form the URL for the correct PyPI JSON API
    pypi_url = PYPI_CONFIG["url_template"].format(
        package_name=package_name, version=current_version
    )
    pypi_host_name = PYPI_CONFIG["name"]

    # 3. Make the request and check the response code
    print(f"Checking for version {current_version} on {pypi_host_name}...")
    try:
        response = requests.get(pypi_url, timeout=10)
    except requests.exceptions.RequestException as e:
        pytest.skip(
            f"Could not connect to {pypi_host_name}. Skipping network test. Error: {e}"
        )

    # 4. If the version exists (200 OK), fail with a clean, formatted message.
    if response.status_code == 200:
        fail_message = (
            f"\n\n{'-' * 28} RELEASE CHECK FAILED {'-' * 28}\n"
            f"Reason:  Version {current_version} of package '{package_name}' "
            f"already exists on {pypi_host_name}.\n"
            f"Action:  Please increment the version in 'pyproject.toml'"
            f" before releasing.\n"
            f"URL:     {pypi_url.replace('/json', '')}\n"
            f"{'-' * 77}"
        )
        pytest.fail(fail_message, pytrace=False)

    elif response.status_code == 404:
        print(
            f"\n\n{'-' * 28} RELEASE CHECK PASSED {'-' * 28}\n"
            f"Version ' {current_version} ' is available on {pypi_host_name}. OK.\n"
            f"{'-' * 77}"
        )
    else:
        pytest.fail(
            f"Received an unexpected status code ({response.status_code}) from\n"
            f" {pypi_host_name}.",
            pytrace=False,
        )
