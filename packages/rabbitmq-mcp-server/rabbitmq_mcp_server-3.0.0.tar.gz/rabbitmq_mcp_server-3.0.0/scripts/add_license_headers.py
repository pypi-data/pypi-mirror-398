#!/usr/bin/env python3
"""
Script to add LGPL v3.0 license headers to all Python source files.
Handles files with shebangs, encoding declarations, and existing headers.
"""

import argparse
import re
from pathlib import Path

LGPL_HEADER = '''"""
Copyright (C) 2025 Luciano Guerche

This file is part of rabbitmq-mcp-server.

rabbitmq-mcp-server is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

rabbitmq-mcp-server is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with rabbitmq-mcp-server. If not, see <https://www.gnu.org/licenses/>.
"""'''

# Patterns to detect existing license headers
LICENSE_PATTERNS = [
    r"LGPL v3\.0",
    r"GNU Lesser General Public License",
    r"GNU LESSER GENERAL PUBLIC LICENSE",
    r"Copyright \(C\)",
    r"This file is part of",
]

# Files to skip
SKIP_PATTERNS = [
    "*/__pycache__/*",
    "*/.*",  # Hidden files/directories
    "*.pyc",
    "*.pyo",
    "*/venv/*",
    "*/.venv/*",
    "*/build/*",
    "*/dist/*",
    "*/.pytest_cache/*",
    "*/.mypy_cache/*",
    "*/.ruff_cache/*",
    "*/htmlcov/*",
    "*/data/vectors/*",
]


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped based on patterns."""
    path_str = str(file_path)
    for pattern in SKIP_PATTERNS:
        if Path(path_str).match(pattern):
            return True
    return False


def has_license_header(content: str) -> bool:
    """Check if file already has a license header."""
    # Check only the first 30 lines for license patterns
    # Must appear in a docstring (triple-quoted) or comment, not in code
    lines = content.split("\n")[:30]

    # Look for our standard license header format
    # It should be in a docstring at the top of the file
    in_docstring = False
    docstring_content = []

    for line in lines:
        stripped = line.strip()

        # Skip shebang and encoding
        if stripped.startswith("#!") or "coding:" in stripped or "coding=" in stripped:
            continue

        # Start of docstring
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            docstring_content.append(line)
            # Check if it's a single-line docstring
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                in_docstring = False
            continue

        # Inside docstring
        if in_docstring:
            docstring_content.append(line)
            if '"""' in line or "'''" in line:
                in_docstring = False
                # Now check if this docstring contains license info
                docstring_text = "\n".join(docstring_content)
                for pattern in LICENSE_PATTERNS:
                    if re.search(pattern, docstring_text, re.IGNORECASE):
                        return True
                docstring_content = []

    return False


def extract_special_lines(content: str) -> tuple[list[str], str]:
    """
    Extract shebang and encoding declaration from the beginning of the file.
    Returns (special_lines, remaining_content).
    """
    lines = content.split("\n")
    special_lines = []
    idx = 0

    # Check for shebang (must be first line)
    if lines and lines[0].startswith("#!"):
        special_lines.append(lines[0])
        idx = 1

    # Check for encoding declaration (must be in first or second line)
    if idx < len(lines) and re.match(r"#.*coding[:=]\s*([-\w.]+)", lines[idx]):
        special_lines.append(lines[idx])
        idx += 1

    remaining_content = "\n".join(lines[idx:])
    return special_lines, remaining_content


def add_header_to_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Add license header to a Python file.
    Returns True if file was modified, False otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"⚠️  Skipping {file_path} (encoding issue)")
        return False

    # Skip if already has license
    if has_license_header(content):
        print(f"✓ {file_path} (already has license)")
        return False

    # Extract special lines (shebang, encoding)
    special_lines, remaining_content = extract_special_lines(content)

    # Remove leading empty lines from remaining content
    remaining_content = remaining_content.lstrip("\n")

    # Build new content
    new_lines = []

    # Add special lines first
    if special_lines:
        new_lines.extend(special_lines)
        new_lines.append("")  # Blank line after special lines

    # Add license header
    new_lines.append(LGPL_HEADER)

    # Add remaining content
    if remaining_content:
        new_lines.append("")  # Blank line after header
        new_lines.append(remaining_content)

    new_content = "\n".join(new_lines)

    if dry_run:
        print(f"🔍 Would add header to: {file_path}")
        return True

    # Write back to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Added header to: {file_path}")
    return True


def find_python_files(root_dir: Path) -> list[Path]:
    """Find all Python files in the directory tree."""
    python_files = []

    for pattern in ["**/*.py"]:
        for file_path in root_dir.glob(pattern):
            if file_path.is_file() and not should_skip_file(file_path):
                python_files.append(file_path)

    return sorted(python_files)


def main():
    parser = argparse.ArgumentParser(
        description="Add LGPL v3.0 license headers to Python source files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if all files have license headers (exit 1 if any missing)",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("src"), Path("scripts"), Path("tests")],
        help="Paths to process (default: src scripts tests)",
    )

    args = parser.parse_args()

    # Collect all Python files
    all_files = []
    for path in args.paths:
        if not path.exists():
            print(f"⚠️  Path does not exist: {path}")
            continue

        if path.is_file():
            if path.suffix == ".py" and not should_skip_file(path):
                all_files.append(path)
        else:
            all_files.extend(find_python_files(path))

    if not all_files:
        print("No Python files found to process.")
        return 0

    print(f"Found {len(all_files)} Python files to check.\n")

    # Process files
    modified_count = 0
    missing_headers = []

    for file_path in all_files:
        was_modified = add_header_to_file(file_path, dry_run=args.dry_run or args.check)
        if was_modified:
            modified_count += 1
            if args.check:
                missing_headers.append(file_path)

    # Summary
    print(f"\n{'='*60}")
    if args.check:
        if missing_headers:
            print(f"❌ {len(missing_headers)} files missing license headers:")
            for path in missing_headers:
                print(f"   - {path}")
            return 1
        else:
            print("✅ All files have license headers!")
            return 0
    elif args.dry_run:
        print(f"Would add headers to {modified_count} files.")
        print("Run without --dry-run to apply changes.")
    else:
        print(f"✅ Added headers to {modified_count} files.")
        print(f"✓ {len(all_files) - modified_count} files already had headers.")

    return 0


if __name__ == "__main__":
    exit(main())
