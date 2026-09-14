"""Pure structural checks for this repository.

Every check receives the repository root it should operate on rather than
resolving paths itself, so that the violation scenarios described in the spec
can be exercised against synthetic trees instead of the real repository, which
is compliant by construction (design decision D6).

Each check raises :class:`StructureProblem` with a message that identifies the
offending element on its own; a check that cannot reach a verdict fails rather
than passing silently.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

# The structural contract, expressed as data: adding an entry here adds a test
# case without touching any logic (design decision D5).
REQUIRED_DIRECTORIES: tuple[str, ...] = (
    "src",
    "tests",
    "openspec",
    "openspec/specs",
    "openspec/changes",
)

PYPROJECT_FILENAME = "pyproject.toml"
PYTHON_VERSION_FILENAME = ".python-version"
OPENSPEC_CONFIG_PATH = "openspec/config.yaml"

REQUIRED_PROJECT_FIELDS: tuple[str, ...] = ("name", "requires-python")

# Only the ">=MAJOR.MINOR" subset of PEP 440 is understood, on purpose: parsing
# the general case would require the `packaging` dependency, which the proposal
# rules out. Anything outside the subset fails loudly (design decision D2).
_MINIMUM_SPECIFIER = re.compile(r">=\s*(\d+)\.(\d+)")
_PINNED_VERSION = re.compile(r"(\d+)\.(\d+)(?:\.\d+)?")

# The OpenSpec configuration is inspected as text rather than parsed as YAML,
# because PyYAML is not installed (design decision D3).
_SCHEMA_DECLARATION = re.compile(r"^schema:\s*\S", re.MULTILINE)


class StructureProblem(Exception):
    """Raised when a structural invariant of the repository is violated."""


def _format_version(version: tuple[int, ...]) -> str:
    return ".".join(str(part) for part in version)


def require_directory(root: Path, relative_path: str) -> None:
    """Require that ``relative_path`` exists under ``root`` and is a directory."""
    target = root / relative_path
    if not target.exists():
        raise StructureProblem(f"required directory is missing: {relative_path}")
    if not target.is_dir():
        raise StructureProblem(
            f"required path exists but is not a directory: {relative_path}"
        )


def load_project_metadata(root: Path) -> dict:
    """Return the ``[project]`` table declared by the project configuration.

    Parsing errors are reported as :class:`StructureProblem` rather than
    propagated as raw decoding exceptions.
    """
    pyproject = root / PYPROJECT_FILENAME
    if not pyproject.is_file():
        raise StructureProblem(
            f"project configuration is missing: {PYPROJECT_FILENAME}"
        )
    try:
        document = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise StructureProblem(
            f"{PYPROJECT_FILENAME} could not be parsed: {error}"
        ) from error

    project = document.get("project")
    if not isinstance(project, dict):
        raise StructureProblem(f"{PYPROJECT_FILENAME} declares no [project] table")
    for field in REQUIRED_PROJECT_FIELDS:
        if field not in project:
            raise StructureProblem(f"missing required field: project.{field}")
    return project


def parse_minimum_python_version(specifier: str) -> tuple[int, int]:
    """Parse the supported subset of a ``requires-python`` specifier."""
    match = _MINIMUM_SPECIFIER.fullmatch(specifier.strip())
    if match is None:
        raise StructureProblem(
            f"unsupported requires-python specifier {specifier!r}: this check only "
            "understands the '>=MAJOR.MINOR' form and must be extended before any "
            "other form can be validated"
        )
    return int(match.group(1)), int(match.group(2))


def parse_pinned_python_version(text: str) -> tuple[int, int]:
    """Parse the contents of the pinned Python version file."""
    match = _PINNED_VERSION.fullmatch(text.strip())
    if match is None:
        raise StructureProblem(
            f"{PYTHON_VERSION_FILENAME} does not contain a recognisable version: "
            f"{text.strip()!r}"
        )
    return int(match.group(1)), int(match.group(2))


def read_pinned_python_version(root: Path) -> tuple[int, int]:
    """Read and parse the Python version pinned for the development environment."""
    pinned = root / PYTHON_VERSION_FILENAME
    if not pinned.is_file():
        raise StructureProblem(
            f"pinned Python version file is missing: {PYTHON_VERSION_FILENAME}"
        )
    return parse_pinned_python_version(pinned.read_text(encoding="utf-8"))


def require_version_at_least(
    version: tuple[int, ...], minimum: tuple[int, ...], label: str
) -> None:
    """Require ``version`` to satisfy ``minimum``, reporting both values on failure."""
    if version < minimum:
        raise StructureProblem(
            f"{label} is {_format_version(version)}, below the minimum "
            f"{_format_version(minimum)} required by requires-python"
        )


def require_openspec_scaffolding(root: Path) -> None:
    """Require the OpenSpec scaffolding to be present and to declare a schema."""
    require_directory(root, "openspec/specs")
    require_directory(root, "openspec/changes")

    config = root / OPENSPEC_CONFIG_PATH
    if not config.is_file():
        raise StructureProblem(
            f"OpenSpec configuration is missing: {OPENSPEC_CONFIG_PATH}"
        )
    if _SCHEMA_DECLARATION.search(config.read_text(encoding="utf-8")) is None:
        raise StructureProblem(
            f"{OPENSPEC_CONFIG_PATH} declares no workflow schema"
        )
