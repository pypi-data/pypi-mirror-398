"""Pre-commit checks for dead links and mpy-cross compilation."""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Set

import pytest
import requests


def find_markdown_files() -> List[Path]:
    """Find all markdown files in the project."""
    root = Path(__file__).parent.parent
    md_files = []
    for ext in ["*.md", "*.MD"]:
        md_files.extend(root.glob(ext))
        md_files.extend(root.glob(f"**/{ext}"))

    # Exclude hidden directories and common ignore patterns
    excluded = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    return [
        f for f in md_files if not any(part.startswith(".") or part in excluded for part in f.parts)
    ]


def extract_urls_from_markdown(file_path: Path) -> Set[str]:
    """Extract all HTTP(S) URLs from a markdown file."""
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    # Match markdown links [text](url) and plain URLs
    url_pattern = r"https?://[^\s\)<>\"\']+"
    urls = set(re.findall(url_pattern, content))

    # Clean up any trailing punctuation that might have been captured
    cleaned_urls = set()
    for url in urls:
        # Remove trailing punctuation and backticks
        url = re.sub(r'[.,;:!?\)`]+$', "", url)
        cleaned_urls.add(url)

    return cleaned_urls


def is_url_valid(url: str, timeout: int = 10) -> tuple[bool, int]:
    """Check if a URL is accessible.

    Returns:
        tuple of (is_valid, http_code)
    """
    # Skip localhost and example URLs
    if "localhost" in url or "example.com" in url or "127.0.0.1" in url:
        return True, 200

    try:
        # Use HEAD request first (faster)
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LinkChecker/1.0)"},
        )

        # Some servers don't support HEAD, try GET if HEAD fails
        if response.status_code >= 400:
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; LinkChecker/1.0)"},
            )

        # Consider 200-399 as valid
        return response.status_code < 400, response.status_code

    except requests.exceptions.Timeout:
        return False, 408  # Request Timeout
    except requests.exceptions.ConnectionError:
        return False, 0  # Connection failed
    except requests.exceptions.RequestException:
        return False, 0  # Other request errors


def find_python_files() -> List[Path]:
    """Find all Python files in the btbricks package."""
    root = Path(__file__).parent.parent
    btbricks_dir = root / "btbricks"

    if not btbricks_dir.exists():
        return []

    py_files = []
    for py_file in btbricks_dir.rglob("*.py"):
        # Skip __pycache__ and other temp directories
        if "__pycache__" not in py_file.parts:
            py_files.append(py_file)

    return py_files


def check_mpy_cross_available() -> bool:
    """Check if mpy-cross is available."""
    # Try to find mpy-cross in venv first
    venv_mpy_cross = Path(__file__).parent.parent / ".venv" / "bin" / "mpy-cross"
    if venv_mpy_cross.exists():
        return True

    # Fall back to checking PATH
    try:
        result = subprocess.run(
            ["mpy-cross", "--version"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def compile_with_mpy_cross(py_file: Path) -> tuple[bool, str]:
    """Try to compile a Python file with mpy-cross.

    Returns:
        tuple of (success, error_message)
    """
    # Find mpy-cross command
    venv_mpy_cross = Path(__file__).parent.parent / ".venv" / "bin" / "mpy-cross"
    mpy_cross_cmd = str(venv_mpy_cross) if venv_mpy_cross.exists() else "mpy-cross"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "temp.mpy"

        try:
            result = subprocess.run(
                [mpy_cross_cmd, str(py_file), "-o", str(output_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr or result.stdout

        except subprocess.TimeoutExpired:
            return False, "Compilation timeout"
        except Exception as e:
            return False, str(e)


class TestDeadLinks:
    """Test for dead links in markdown files."""

    def test_no_dead_links(self):
        """Check that all links in markdown files are valid."""
        md_files = find_markdown_files()

        if not md_files:
            pytest.skip("No markdown files found")

        all_urls = set()
        url_sources = {}  # Track which file each URL came from

        for md_file in md_files:
            urls = extract_urls_from_markdown(md_file)
            for url in urls:
                all_urls.add(url)
                if url not in url_sources:
                    url_sources[url] = set()
                url_sources[url].add(md_file.name)

        if not all_urls:
            pytest.skip("No URLs found in markdown files")

        dead_links = []

        for url in sorted(all_urls):
            is_valid, http_code = is_url_valid(url)
            if not is_valid:
                sources = ", ".join(sorted(url_sources[url]))
                dead_links.append(f"{url} (HTTP {http_code}) in {sources}")

        if dead_links:
            error_msg = f"Found {len(dead_links)} dead link(s):\n"
            error_msg += "\n".join(f"  - {link}" for link in dead_links)
            pytest.fail(error_msg)


class TestMpyCrossCompilation:
    """Test that all Python files compile with mpy-cross."""

    def test_mpy_cross_installed(self):
        """Check that mpy-cross is available."""
        if not check_mpy_cross_available():
            pytest.fail(
                "mpy-cross is not installed or not available in PATH.\n"
                "Install with: pip install mpy-cross"
            )

    def test_all_files_compile(self):
        """Check that all Python files in btbricks/ compile with mpy-cross."""
        if not check_mpy_cross_available():
            pytest.skip("mpy-cross not available")

        py_files = find_python_files()

        if not py_files:
            pytest.skip("No Python files found in btbricks/")

        failed_compilations = []

        for py_file in py_files:
            success, error = compile_with_mpy_cross(py_file)
            if not success:
                failed_compilations.append(f"{py_file.name}: {error}")

        if failed_compilations:
            error_msg = f"Failed to compile {len(failed_compilations)} file(s) with mpy-cross:\n"
            error_msg += "\n".join(f"  - {failure}" for failure in failed_compilations)
            pytest.fail(error_msg)
