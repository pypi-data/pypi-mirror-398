"""Utility functions for handling .gitignore files across different tools."""

import logging
import os
from pathlib import Path
from typing import Any, List, Tuple

logger = logging.getLogger(__name__)


def find_gitignore_files(root_dir: str) -> List[Tuple[Path, str]]:
    """
    Recursively find all .gitignore files in the directory tree.
    Returns a list of tuples: (gitignore_path, relative_path_from_root)
    """
    gitignore_files = []
    root_path = Path(root_dir).resolve()

    # Handle the case where root_dir is '.'
    if str(root_path) == str(Path(".").resolve()):
        root_path = Path.cwd()

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Convert to Path object and resolve any relative paths
        dirpath = Path(dirpath).resolve()

        # Skip .git directories and their contents
        if ".git" in str(dirpath).split(os.sep):
            dirnames[:] = []  # Don't recurse into .git directories
            continue

        if ".gitignore" in filenames:
            gitignore_path = dirpath / ".gitignore"
            try:
                rel_path = (
                    str(dirpath.relative_to(root_path)) if dirpath != root_path else ""
                )
                gitignore_files.append((gitignore_path, rel_path))
            except ValueError as e:
                # This can happen if the path is not relative to root_path
                logger.debug(f"Skipping {gitignore_path}: {e}")
                continue

    return gitignore_files


def parse_gitignore(gitignore_path: Path, base_path: str = "") -> List[str]:
    """
    Parse a .gitignore file and return patterns with proper paths.
    base_path is the path from project root to the directory containing this .gitignore.
    """
    patterns = []

    # Normalize base_path to use forward slashes and remove any leading/trailing slashes
    if base_path:
        base_path = base_path.replace("\\", "/").strip("/")

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Handle negated patterns (starting with !)
                is_negated = line.startswith("!")
                if is_negated:
                    line = line[1:]

                # Skip empty lines after removing negation
                if not line:
                    continue

                # Handle patterns with or without leading slash
                if line.startswith("/"):
                    # Pattern is relative to this .gitignore's directory
                    pattern = f"{base_path}/{line[1:]}" if base_path else line[1:]
                elif line.startswith("**/"):
                    # Pattern should match in all subdirectories
                    pattern = f"**/{line[3:]}"
                else:
                    # Pattern is relative to this .gitignore's directory
                    if base_path:
                        pattern = f"{base_path}/**/{line}"
                    else:
                        pattern = f"**/{line}"

                # Normalize path separators
                pattern = pattern.replace("\\", "/")

                # Handle directory patterns (ending with /)
                if line.endswith("/"):
                    pattern = pattern.rstrip("/") + "/**"

                # Re-add negation if it was present
                if is_negated:
                    pattern = f"!{pattern}"

                patterns.append(pattern)
    except UnicodeDecodeError:
        logger.warning(f"Skipping unreadable .gitignore file: {gitignore_path}")
    except Exception as e:
        logger.warning(f"Error reading {gitignore_path}: {e}")

    return patterns


def normalize_patterns_for_tool(patterns: List[str], tool: str) -> List[Any]:
    """
    Convert gitignore patterns to tool-specific patterns.
    """
    result = []

    # Deduplicate patterns while preserving order
    seen = set()
    unique_patterns = []
    for p in patterns:
        if p and p not in seen:
            seen.add(p)
            unique_patterns.append(p)

    logger.debug(f"Normalizing {len(unique_patterns)} patterns for {tool}")

    for pattern in unique_patterns:
        # Handle negated patterns
        is_negated = pattern.startswith("!")
        if is_negated:
            pattern = pattern[1:]

        # Skip empty patterns
        if not pattern:
            continue

        try:
            if tool == "sonarqube":
                # Convert to SonarQube exclusions (doesn't support negations)
                if not is_negated:
                    # SonarQube uses ant-style patterns
                    if pattern.endswith("/**"):
                        # Directory pattern
                        result.append(pattern)
                    elif pattern.endswith("/"):
                        result.append(f"{pattern}**")
                    elif "/" not in pattern and not pattern.startswith("**/"):
                        # Simple filename pattern
                        result.append(f"**/{pattern}")
                    else:
                        # Already in correct format
                        result.append(pattern)

            elif tool == "trivy":
                # For trivy, we'll use --skip-files and --skip-dirs
                # Note: Trivy doesn't support negated patterns in skip lists
                if not is_negated:
                    if pattern.endswith("/**") or pattern.endswith("/"):
                        # Directory pattern
                        dir_pattern = pattern.rstrip("/").rstrip("**")
                        result.append(("dir", dir_pattern))
                    else:
                        # File pattern
                        result.append(("file", pattern))

            elif tool == "semgrep":
                # For semgrep, create .semgrepignore
                # Convert gitignore patterns to semgrep format
                pattern = pattern.replace("\\", "/")  # Normalize path separators

                # Handle directory patterns
                if pattern.endswith("/**"):
                    pattern = pattern[:-3] + "/"  # Convert to directory pattern

                # Semgrep doesn't support negated patterns in .semgrepignore
                if not is_negated:
                    # Remove leading **/ as semgrep matches from project root
                    if pattern.startswith("**/"):
                        pattern = pattern[3:]
                    result.append(pattern)

        except Exception as e:
            logger.warning(f"Error processing pattern '{pattern}' for {tool}: {e}")

    # Log the number of patterns for each type
    if tool == "trivy":
        file_patterns = [p[1] for p in result if p[0] == "file"]
        dir_patterns = [p[1] for p in result if p[0] == "dir"]
        logger.debug(
            f"Trivy patterns - Files: {len(file_patterns)}, Directories: {len(dir_patterns)}"
        )
    else:
        logger.debug(f"{tool.capitalize()} patterns: {len(result)}")

    return result


def get_tool_specific_exclusions(project_root: str, tool: str):
    """
    Get exclusions for a specific tool based on .gitignore files.
    Returns either a list of patterns or a tuple of (file_patterns, dir_patterns) for Trivy.
    """
    try:
        gitignore_files = find_gitignore_files(project_root)
        all_patterns = []

        # Process .gitignore files from root to leaves
        for gitignore_path, rel_path in sorted(
            gitignore_files, key=lambda x: len(str(x[0]).split(os.sep))
        ):
            patterns = parse_gitignore(gitignore_path, rel_path)
            all_patterns.extend(patterns)

        tool_patterns = normalize_patterns_for_tool(all_patterns, tool)

        if tool == "semgrep":
            # Add default exclusions for Semgrep
            default_semgrep_patterns = [
                "*.min.js",
                "*.min.css",
                "*-bundle.js",
                "*-bundle.min.js",
                "*.map",
                "node_modules/",
                "bower_components/",
                "dist/",
                "build/",
                "vendor/",
            ]
            # Normalize and add default patterns
            default_patterns_normalized = normalize_patterns_for_tool(
                default_semgrep_patterns, tool
            )
            # Combine with existing patterns, avoiding duplicates
            tool_patterns = list(set(tool_patterns + default_patterns_normalized))

        if tool == "trivy":
            # For trivy, separate files and dirs
            file_patterns = [p[1] for p in tool_patterns if p[0] == "file"]
            dir_patterns = [p[1] for p in tool_patterns if p[0] == "dir"]
            return file_patterns, dir_patterns
        else:
            return tool_patterns

    except Exception as e:
        logger.warning(f"Error processing .gitignore files: {e}")
        if tool == "trivy":
            return [], []
        return []
