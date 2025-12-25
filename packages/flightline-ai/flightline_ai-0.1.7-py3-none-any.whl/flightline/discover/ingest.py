"""File ingestion and project detection.

Handles:
- File enumeration respecting .gitignore
- Language detection
- Project type/framework detection
"""

import os
from pathlib import Path
from typing import Optional

import pathspec

from flightline.discover.schema import ProjectSignals, RepoMetadata

# =============================================================================
# FILE PATTERNS
# =============================================================================

# Default ignore patterns (always applied)
DEFAULT_IGNORES = [
    ".git/",
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    ".env/",
    "dist/",
    "build/",
    ".next/",
    "*.pyc",
    "*.pyo",
    "*.egg-info/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "coverage/",
    ".coverage",
    "*.min.js",
    "*.bundle.js",
    "*.map",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
]

# Language detection by extension
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}

# Supported languages for AI detection
SUPPORTED_LANGUAGES = {"python", "javascript", "typescript"}

# Framework detection files
FRAMEWORK_MARKERS = {
    # Python frameworks
    "fastapi": ["main.py", "app.py"],  # + check for fastapi import
    "django": ["manage.py", "settings.py"],
    "flask": ["app.py"],  # + check for flask import
    # JS/TS frameworks
    "nextjs": ["next.config.js", "next.config.mjs", "next.config.ts"],
    "express": [],  # detect via package.json deps
    "remix": ["remix.config.js"],
    "nuxt": ["nuxt.config.js", "nuxt.config.ts"],
}

# AI SDK markers in package files
AI_SDK_MARKERS = {
    "openai": ["openai"],
    "anthropic": ["@anthropic-ai/sdk", "anthropic"],
    "google": ["@google/generative-ai", "google-generativeai"],
    "mistral": ["@mistralai/mistralai", "mistralai"],
    "langchain": ["langchain", "@langchain/core"],
    "llamaindex": ["llama-index", "llamaindex"],
}

# Validation library markers
VALIDATION_MARKERS = {
    "zod": ["zod"],
    "pydantic": ["pydantic"],
    "yup": ["yup"],
    "joi": ["joi"],
    "jsonschema": ["jsonschema"],
}


# =============================================================================
# FILE DISCOVERY
# =============================================================================


class FileIndex:
    """Index of files in a repository."""

    def __init__(self, root: Path, files: list[Path], languages: set[str]):
        self.root = root
        self.files = files
        self.languages = languages

    def files_by_language(self, language: str) -> list[Path]:
        """Get files for a specific language."""
        extensions = [ext for ext, lang in LANGUAGE_EXTENSIONS.items() if lang == language]
        return [f for f in self.files if f.suffix in extensions]

    @property
    def python_files(self) -> list[Path]:
        return self.files_by_language("python")

    @property
    def javascript_files(self) -> list[Path]:
        return self.files_by_language("javascript")

    @property
    def typescript_files(self) -> list[Path]:
        return self.files_by_language("typescript")


def load_gitignore(root: Path) -> Optional[pathspec.PathSpec]:
    """Load .gitignore patterns from repository root."""
    gitignore_path = root / ".gitignore"

    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        patterns = f.read().splitlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def should_ignore(
    path: Path,
    root: Path,
    gitignore_spec: Optional[pathspec.PathSpec],
    default_spec: pathspec.PathSpec,
) -> bool:
    """Check if a path should be ignored."""
    try:
        rel_path = path.relative_to(root)
    except ValueError:
        return True

    rel_str = str(rel_path)

    # Check default ignores
    if default_spec.match_file(rel_str):
        return True

    # Check .gitignore
    if gitignore_spec and gitignore_spec.match_file(rel_str):
        return True

    return False


def enumerate_files(
    root: Path,
    max_files: int = 5000,
    languages: Optional[set[str]] = None,
) -> FileIndex:
    """
    Enumerate files in a repository.

    Args:
        root: Repository root directory
        max_files: Maximum number of files to index
        languages: Languages to include (None = all supported)

    Returns:
        FileIndex with discovered files
    """
    root = root.resolve()

    # Build ignore specs
    default_spec = pathspec.PathSpec.from_lines("gitwildmatch", DEFAULT_IGNORES)
    gitignore_spec = load_gitignore(root)

    # Filter extensions by requested languages
    if languages:
        valid_extensions = {ext for ext, lang in LANGUAGE_EXTENSIONS.items() if lang in languages}
    else:
        valid_extensions = set(LANGUAGE_EXTENSIONS.keys())

    files: list[Path] = []
    detected_languages: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        # Skip ignored directories (modify dirnames in-place)
        dirnames[:] = [d for d in dirnames if not should_ignore(current_dir / d, root, gitignore_spec, default_spec)]

        for filename in filenames:
            if len(files) >= max_files:
                break

            file_path = current_dir / filename

            # Check extension
            if file_path.suffix not in valid_extensions:
                continue

            # Check ignore patterns
            if should_ignore(file_path, root, gitignore_spec, default_spec):
                continue

            files.append(file_path)
            lang = LANGUAGE_EXTENSIONS.get(file_path.suffix)
            if lang:
                detected_languages.add(lang)

        if len(files) >= max_files:
            break

    return FileIndex(root, files, detected_languages)


# =============================================================================
# PROJECT DETECTION
# =============================================================================


def detect_project_signals(root: Path) -> ProjectSignals:
    """
    Detect project frameworks, AI SDKs, and validation libraries.

    Args:
        root: Repository root directory

    Returns:
        ProjectSignals with detected tech stack
    """
    signals = ProjectSignals()

    # Check package.json for JS/TS projects
    package_json_path = root / "package.json"
    if package_json_path.exists():
        _detect_from_package_json(package_json_path, signals)

    # Check pyproject.toml for Python projects
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        _detect_from_pyproject(pyproject_path, signals)

    # Check requirements.txt
    requirements_path = root / "requirements.txt"
    if requirements_path.exists():
        _detect_from_requirements(requirements_path, signals)

    # Check for framework marker files
    _detect_framework_files(root, signals)

    return signals


def _detect_from_package_json(path: Path, signals: ProjectSignals) -> None:
    """Parse package.json for dependencies."""
    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    # Collect all dependencies
    deps = set()
    for key in ["dependencies", "devDependencies", "peerDependencies"]:
        if key in data and isinstance(data[key], dict):
            deps.update(data[key].keys())

    # Detect AI SDKs
    for sdk, markers in AI_SDK_MARKERS.items():
        if any(marker in deps for marker in markers):
            if sdk not in signals.ai_sdks:
                signals.ai_sdks.append(sdk)

    # Detect validation libraries
    for lib, markers in VALIDATION_MARKERS.items():
        if any(marker in deps for marker in markers):
            if lib not in signals.validation_libraries:
                signals.validation_libraries.append(lib)

    # Detect frameworks
    if "next" in deps:
        if "nextjs" not in signals.frameworks:
            signals.frameworks.append("nextjs")
    if "express" in deps:
        if "express" not in signals.frameworks:
            signals.frameworks.append("express")
    if "remix" in deps or "@remix-run/node" in deps:
        if "remix" not in signals.frameworks:
            signals.frameworks.append("remix")


def _detect_from_pyproject(path: Path, signals: ProjectSignals) -> None:
    """Parse pyproject.toml for dependencies."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return

    content_lower = content.lower()

    # Simple string matching for common packages
    # (avoiding toml dependency for simplicity)

    # AI SDKs
    if "openai" in content_lower:
        if "openai" not in signals.ai_sdks:
            signals.ai_sdks.append("openai")
    if "anthropic" in content_lower:
        if "anthropic" not in signals.ai_sdks:
            signals.ai_sdks.append("anthropic")
    if "google-generativeai" in content_lower:
        if "google" not in signals.ai_sdks:
            signals.ai_sdks.append("google")
    if "mistralai" in content_lower:
        if "mistral" not in signals.ai_sdks:
            signals.ai_sdks.append("mistral")
    if "langchain" in content_lower:
        if "langchain" not in signals.ai_sdks:
            signals.ai_sdks.append("langchain")

    # Validation
    if "pydantic" in content_lower:
        if "pydantic" not in signals.validation_libraries:
            signals.validation_libraries.append("pydantic")

    # Frameworks
    if "fastapi" in content_lower:
        if "fastapi" not in signals.frameworks:
            signals.frameworks.append("fastapi")
    if "django" in content_lower:
        if "django" not in signals.frameworks:
            signals.frameworks.append("django")
    if "flask" in content_lower:
        if "flask" not in signals.frameworks:
            signals.frameworks.append("flask")


def _detect_from_requirements(path: Path, signals: ProjectSignals) -> None:
    """Parse requirements.txt for dependencies."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return

    lines = content.lower().splitlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Extract package name (before version specifier)
        package = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].strip()

        # AI SDKs
        if package == "openai":
            if "openai" not in signals.ai_sdks:
                signals.ai_sdks.append("openai")
        elif package == "anthropic":
            if "anthropic" not in signals.ai_sdks:
                signals.ai_sdks.append("anthropic")
        elif package == "google-generativeai":
            if "google" not in signals.ai_sdks:
                signals.ai_sdks.append("google")
        elif package == "mistralai":
            if "mistral" not in signals.ai_sdks:
                signals.ai_sdks.append("mistral")
        elif package.startswith("langchain"):
            if "langchain" not in signals.ai_sdks:
                signals.ai_sdks.append("langchain")

        # Validation
        elif package == "pydantic":
            if "pydantic" not in signals.validation_libraries:
                signals.validation_libraries.append("pydantic")

        # Frameworks
        elif package == "fastapi":
            if "fastapi" not in signals.frameworks:
                signals.frameworks.append("fastapi")
        elif package == "django":
            if "django" not in signals.frameworks:
                signals.frameworks.append("django")
        elif package == "flask":
            if "flask" not in signals.frameworks:
                signals.frameworks.append("flask")


def _detect_framework_files(root: Path, signals: ProjectSignals) -> None:
    """Detect frameworks by marker files."""
    # Next.js
    for marker in FRAMEWORK_MARKERS["nextjs"]:
        if (root / marker).exists():
            if "nextjs" not in signals.frameworks:
                signals.frameworks.append("nextjs")
            break

    # Remix
    for marker in FRAMEWORK_MARKERS["remix"]:
        if (root / marker).exists():
            if "remix" not in signals.frameworks:
                signals.frameworks.append("remix")
            break

    # Django
    if (root / "manage.py").exists():
        if "django" not in signals.frameworks:
            signals.frameworks.append("django")


def build_repo_metadata(root: Path, file_index: FileIndex) -> RepoMetadata:
    """Build repository metadata from file index."""
    return RepoMetadata(
        root=str(root.resolve()),
        files_scanned=len(file_index.files),
        languages=sorted(file_index.languages),
    )
