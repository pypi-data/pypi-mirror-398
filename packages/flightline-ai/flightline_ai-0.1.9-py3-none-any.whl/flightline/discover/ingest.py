"""File ingestion and project detection.

Handles:
- File enumeration respecting .gitignore
- Language detection
- Project type/framework detection
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Union

import pathspec

from flightline.discover.schema import ProjectSignals, RepoMetadata

# =============================================================================
# FILE PATTERNS
# =============================================================================

# Map file extensions to languages
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}

# Directories to skip by default (even if not in .gitignore)
DEFAULT_IGNORE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    ".next",
    "dist",
    "build",
    "coverage",
}


# =============================================================================
# FILE INDEX
# =============================================================================


class FileIndex:
    """Index of files in a repository."""

    def __init__(self, root: Path, files: List[Path], languages: Set[str]):
        self.root = root
        self.files = files
        self.languages = languages

    def files_by_language(self, language: str) -> List[Path]:
        """Get files for a specific language."""
        extensions = [ext for ext, lang in LANGUAGE_EXTENSIONS.items() if lang == language]
        return [f for f in self.files if f.suffix in extensions]

    @property
    def python_files(self) -> List[Path]:
        return self.files_by_language("python")

    @property
    def javascript_files(self) -> List[Path]:
        return self.files_by_language("javascript")

    @property
    def typescript_files(self) -> List[Path]:
        return self.files_by_language("typescript")


# =============================================================================
# INGESTION LOGIC
# =============================================================================


def enumerate_files(
    root: Path,
    languages: Optional[Set[str]] = None,
    max_files: int = 5000,
) -> FileIndex:
    """
    Find all relevant source files in the root directory.

    Args:
        root: Base directory to scan
        languages: Optional list of languages to include
        max_files: Safety limit on total files scanned

    Returns:
        FileIndex containing the list of files
    """
    project_ignore_spec = load_project_ignore(root)
    default_spec = pathspec.PathSpec.from_lines("gitwildmatch", list(DEFAULT_IGNORE_DIRS))

    if languages:
        valid_extensions = {ext for ext, lang in LANGUAGE_EXTENSIONS.items() if lang in languages}
    else:
        valid_extensions = set(LANGUAGE_EXTENSIONS.keys())

    files: List[Path] = []
    detected_languages: Set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        # Skip ignored directories (modify dirnames in-place)
        dirnames[:] = [
            d for d in dirnames if not should_ignore(current_dir / d, root, project_ignore_spec, default_spec)
        ]

        for filename in filenames:
            if len(files) >= max_files:
                break

            file_path = current_dir / filename

            # Check extension
            if file_path.suffix.lower() in valid_extensions:
                # Check if file is ignored
                if not should_ignore(file_path, root, project_ignore_spec, default_spec):
                    files.append(file_path)
                    lang = LANGUAGE_EXTENSIONS.get(file_path.suffix.lower())
                    if lang:
                        detected_languages.add(lang)

    return FileIndex(root, files, detected_languages)


def should_ignore(
    path: Path, root: Path, ignore_spec: Optional[pathspec.PathSpec], default_spec: pathspec.PathSpec
) -> bool:
    """Check if a file or directory should be ignored."""
    # Convert absolute path to relative for pathspec matching
    try:
        rel_path = str(path.relative_to(root))
    except ValueError:
        return True

    # 1. Check default hardcoded ignores
    if default_spec.match_file(rel_path):
        return True

    # 2. Check .gitignore + .flightlineignore
    if ignore_spec and ignore_spec.match_file(rel_path):
        return True

    return False


def _read_ignore_file(path: Path) -> List[str]:
    """Read ignore file lines safely."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.readlines()
    except Exception:
        return []


def load_project_ignore(root: Path) -> Optional[pathspec.PathSpec]:
    """Load and parse ignore rules from .gitignore and .flightlineignore (gitignore syntax)."""
    lines: List[str] = []

    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        lines.extend(_read_ignore_file(gitignore_path))

    flightlineignore_path = root / ".flightlineignore"
    if flightlineignore_path.exists():
        lines.extend(_read_ignore_file(flightlineignore_path))

    if not lines:
        return None

    try:
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)
    except Exception:
        return None


# =============================================================================
# PROJECT DETECTION
# =============================================================================


def detect_project_signals(file_index: Union[FileIndex, Path]) -> ProjectSignals:
    """Identify project frameworks and libraries from the file index or directory."""
    # Handle direct Path input for testing or simple usage
    if isinstance(file_index, Path):
        root = file_index
        languages: Set[str] = set()
    else:
        root = file_index.root
        languages = file_index.languages

    signals = ProjectSignals(
        frameworks=[],
        ai_sdks=[],
        validation_libraries=[],
    )

    # 1. Framework detection via package.json / requirements.txt
    pkg_json = root / "package.json"
    if pkg_json.exists():
        content = pkg_json.read_text(encoding="utf-8", errors="ignore")
        if "next" in content:
            signals.frameworks.append("nextjs")
        if "express" in content:
            signals.frameworks.append("express")
        if "zod" in content:
            signals.validation_libraries.append("zod")
        if "openai" in content:
            signals.ai_sdks.append("openai")
        if "anthropic" in content:
            signals.ai_sdks.append("anthropic")

    req_txt = root / "requirements.txt"
    if req_txt.exists():
        content = req_txt.read_text(encoding="utf-8", errors="ignore")
        if "fastapi" in content:
            signals.frameworks.append("fastapi")
        if "flask" in content:
            signals.frameworks.append("flask")
        if "pydantic" in content:
            signals.validation_libraries.append("pydantic")
        if "openai" in content:
            signals.ai_sdks.append("openai")
        if "anthropic" in content:
            signals.ai_sdks.append("anthropic")

    # 2. Add language signals
    if "typescript" in languages:
        signals.frameworks.append("typescript")

    return signals


def build_repo_metadata(file_index: FileIndex) -> RepoMetadata:
    """Construct metadata for the repository."""
    return RepoMetadata(
        root=str(file_index.root),
        files_scanned=len(file_index.files),
        languages=list(file_index.languages),
    )
