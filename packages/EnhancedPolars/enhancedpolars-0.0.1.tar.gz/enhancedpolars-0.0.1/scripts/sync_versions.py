#!/usr/bin/env python3
"""
Sync package versions from pyproject.toml to documentation files.

This script reads dependency versions from pyproject.toml and updates:
- README.md (Requirements section)
- docs/getting-started.md (if exists)

Usage:
    python scripts/sync_versions.py [--check]

Options:
    --check    Check if files are in sync without modifying (exits 1 if out of sync)
"""

import re
import sys
import tomllib
from pathlib import Path
from typing import Dict, Tuple


def parse_version_spec(spec: str) -> Tuple[str, str]:
    """
    Parse a version specifier like 'polars>=1.25.0,<2.0.0' into (package, min_version).

    Returns:
        Tuple of (package_name, minimum_version_display)
    """
    # Extract package name
    match = re.match(r'^([a-zA-Z0-9_-]+)', spec)
    if not match:
        return spec, ""

    package = match.group(1)

    # Extract minimum version (look for >= or ==)
    version_match = re.search(r'>=([0-9.]+)', spec)
    if version_match:
        return package, version_match.group(1) + "+"

    version_match = re.search(r'==([0-9.]+)', spec)
    if version_match:
        return package, version_match.group(1)

    return package, ""


def read_pyproject() -> Dict:
    """Read and parse pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def get_requirements_from_pyproject(config: Dict) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    """
    Extract requirements from pyproject.toml.

    Returns:
        Tuple of:
        - Dict mapping core package names to version strings
        - Dict mapping optional extra names to their packages/versions
    """
    project = config.get("project", {})

    core_requirements = {}
    optional_requirements = {}

    # Python version
    python_requires = project.get("requires-python", "")
    if python_requires:
        version_match = re.search(r'>=([0-9.]+)', python_requires)
        if version_match:
            core_requirements["Python"] = version_match.group(1) + "+"

    # Core dependencies
    dependencies = project.get("dependencies", [])
    for dep in dependencies:
        package, version = parse_version_spec(dep)
        if version:
            core_requirements[package] = version

    # Optional dependencies
    optional_deps = project.get("optional-dependencies", {})
    for extra_name, deps in optional_deps.items():
        if extra_name == "all":
            continue  # Skip the 'all' aggregate
        optional_requirements[extra_name] = {}
        for dep in deps:
            package, version = parse_version_spec(dep)
            if version:
                optional_requirements[extra_name][package] = version

    return core_requirements, optional_requirements


def generate_readme_requirements(
    core_reqs: Dict[str, str],
    optional_reqs: Dict[str, Dict[str, str]]
) -> str:
    """Generate the Requirements section markdown for README."""
    lines = ["## Requirements", "", "### Core Dependencies", ""]

    # Core packages in a specific order
    core_order = ["Python", "polars", "numpy", "pandas", "pyarrow"]
    for pkg in core_order:
        if pkg in core_reqs:
            if pkg == "Python":
                lines.append(f"- **{pkg}** {core_reqs[pkg]}")
            else:
                lines.append(f"- **{pkg}** >= {core_reqs[pkg].rstrip('+')}")

    # Other core packages
    other_core = ["tqdm", "python-dateutil", "joblib"]
    other_found = [pkg for pkg in other_core if pkg in core_reqs]
    if other_found:
        lines.append(f"- Plus: {', '.join(other_found)}")

    lines.append("")

    # Optional dependencies
    if optional_reqs:
        lines.append("### Optional Dependencies")
        lines.append("")
        lines.append("Install with extras for additional functionality:")
        lines.append("")
        lines.append("```bash")
        lines.append("# For scientific computing (interpolation, hypothesis tests)")
        lines.append('pip install "EnhancedPolars[sci]"')
        lines.append("")
        lines.append("# For ML preprocessing (scalers, encoders)")
        lines.append('pip install "EnhancedPolars[ml]"')
        lines.append("")
        lines.append("# Install all optional dependencies")
        lines.append('pip install "EnhancedPolars[all]"')
        lines.append("```")
        lines.append("")

        # List what each extra provides
        extra_descriptions = {
            "sci": "Scientific computing",
            "ml": "Machine learning",
        }
        for extra, packages in optional_reqs.items():
            desc = extra_descriptions.get(extra, extra)
            pkg_list = ", ".join([f"{pkg} >= {ver.rstrip('+')}" for pkg, ver in packages.items()])
            lines.append(f"- **`[{extra}]`** - {desc}: {pkg_list}")

        lines.append("")

    return "\n".join(lines)


def generate_requirements_table(
    core_reqs: Dict[str, str],
    optional_reqs: Dict[str, Dict[str, str]]
) -> str:
    """Generate a requirements table for detailed docs."""
    lines = [
        "### Core Dependencies",
        "",
        "| Package | Minimum Version | Purpose |",
        "|---------|-----------------|---------|",
    ]

    package_purposes = {
        "Python": "Runtime",
        "polars": "Core DataFrame library",
        "numpy": "Numerical operations",
        "pandas": "DataFrame interoperability",
        "pyarrow": "Arrow format support",
        "tqdm": "Progress bars",
        "python-dateutil": "Date parsing",
        "joblib": "Model serialization",
        "SQLUtilities": "SQL dialect support",
        "CoreUtilities": "Type definitions",
    }

    for pkg, version in core_reqs.items():
        purpose = package_purposes.get(pkg, "")
        lines.append(f"| {pkg} | {version} | {purpose} |")

    if optional_reqs:
        lines.append("")
        lines.append("### Optional Dependencies")
        lines.append("")
        lines.append("| Package | Minimum Version | Extra | Purpose |")
        lines.append("|---------|-----------------|-------|---------|")

        optional_purposes = {
            "scipy": "Statistical functions, interpolation",
            "scikit-learn": "ML preprocessing, scalers, encoders",
        }

        for extra, packages in optional_reqs.items():
            for pkg, version in packages.items():
                purpose = optional_purposes.get(pkg, "")
                lines.append(f"| {pkg} | {version} | `[{extra}]` | {purpose} |")

        lines.append("")
        lines.append("Install optional dependencies with:")
        lines.append("")
        lines.append("```bash")
        lines.append('pip install "EnhancedPolars[all]"  # All optional deps')
        lines.append('pip install "EnhancedPolars[sci]"  # Scientific computing only')
        lines.append('pip install "EnhancedPolars[ml]"   # ML preprocessing only')
        lines.append("```")

    return "\n".join(lines)


def update_readme(
    core_reqs: Dict[str, str],
    optional_reqs: Dict[str, Dict[str, str]],
    check_only: bool = False
) -> bool:
    """
    Update the Requirements section in README.md.

    Returns:
        True if file was updated (or would be updated in check mode)
    """
    readme_path = Path(__file__).parent.parent / "README.md"

    with open(readme_path, "r") as f:
        content = f.read()

    # Find the Requirements section (between ## Requirements and next ## or ---)
    requirements_pattern = r'(## Requirements\s*\n)(.*?)(\n---|\n## [A-Z])'

    # Generate new requirements content
    new_requirements = generate_readme_requirements(core_reqs, optional_reqs)

    match = re.search(requirements_pattern, content, re.DOTALL)
    if match:
        old_section = match.group(1) + match.group(2)

        if old_section.strip() != new_requirements.strip():
            if check_only:
                python_ver = core_reqs.get("Python", "3.13+")
                polars_ver = core_reqs.get("polars", "1.25.0+")
                print("README.md requirements section is out of sync:")
                print(f"  Expected Python: {python_ver}")
                print(f"  Expected polars: >= {polars_ver.rstrip('+')}")
                return True

            # Replace the section
            new_content = content[:match.start()] + new_requirements + "\n" + match.group(3) + content[match.end():]

            with open(readme_path, "w") as f:
                f.write(new_content)

            print("Updated README.md requirements section")
            return True

    return False


def update_getting_started(
    core_reqs: Dict[str, str],
    optional_reqs: Dict[str, Dict[str, str]],
    check_only: bool = False
) -> bool:
    """Update requirements in docs/getting-started.md if it exists."""
    docs_path = Path(__file__).parent.parent / "docs" / "getting-started.md"

    if not docs_path.exists():
        return False

    with open(docs_path, "r") as f:
        content = f.read()

    # Look for a requirements/dependencies section with a table
    requirements_pattern = r'(###? (?:Requirements|Dependencies|Prerequisites)\s*\n)(.*?)(\n## [A-Z]|\Z)'

    match = re.search(requirements_pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        existing_section = match.group(2)

        # Check if all required packages are present with correct versions
        out_of_sync = False

        # Check core requirements
        for pkg, version in core_reqs.items():
            pkg_pattern = rf'\|\s*{re.escape(pkg)}\s*\|\s*{re.escape(version)}\s*\|'
            if not re.search(pkg_pattern, existing_section):
                out_of_sync = True
                if check_only:
                    print(f"  Missing or wrong version for {pkg}: expected {version}")
                break

        # Check optional requirements
        if not out_of_sync:
            for extra, packages in optional_reqs.items():
                for pkg, version in packages.items():
                    pkg_pattern = rf'\|\s*{re.escape(pkg)}\s*\|\s*{re.escape(version)}\s*\|'
                    if not re.search(pkg_pattern, existing_section):
                        out_of_sync = True
                        if check_only:
                            print(f"  Missing or wrong version for optional {pkg}: expected {version}")
                        break

        if out_of_sync:
            if check_only:
                print("docs/getting-started.md requirements section is out of sync")
                return True

            # Generate table format for docs
            table = generate_requirements_table(core_reqs, optional_reqs)
            new_section = match.group(1) + "\n" + table + "\n\n"

            new_content = content[:match.start()] + new_section + match.group(3) + content[match.end():]

            with open(docs_path, "w") as f:
                f.write(new_content)

            print("Updated docs/getting-started.md requirements section")
            return True

    return False


def main():
    check_only = "--check" in sys.argv

    # Read pyproject.toml
    config = read_pyproject()
    core_reqs, optional_reqs = get_requirements_from_pyproject(config)

    print("Core requirements from pyproject.toml:")
    for pkg, version in core_reqs.items():
        print(f"  {pkg}: {version}")

    print("\nOptional requirements:")
    for extra, packages in optional_reqs.items():
        print(f"  [{extra}]:")
        for pkg, version in packages.items():
            print(f"    {pkg}: {version}")
    print()

    # Update files
    changed = False
    changed |= update_readme(core_reqs, optional_reqs, check_only)
    changed |= update_getting_started(core_reqs, optional_reqs, check_only)

    if check_only:
        if changed:
            print("\nFiles are out of sync. Run 'python scripts/sync_versions.py' to update.")
            sys.exit(1)
        else:
            print("All files are in sync.")
            sys.exit(0)
    else:
        if not changed:
            print("All files already up to date.")


if __name__ == "__main__":
    main()
