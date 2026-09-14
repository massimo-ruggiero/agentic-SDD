"""Structural validation of the repository layout and toolchain metadata.

Each requirement of the `project-structure-validation` capability is exercised
twice: once against the real repository, to confirm current compliance, and
once against a synthetic tree, to cover the violation scenarios that the real
repository cannot produce (design decision D6).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.structure_checks import (
    OPENSPEC_CONFIG_PATH,
    PYPROJECT_FILENAME,
    PYTHON_VERSION_FILENAME,
    REQUIRED_DIRECTORIES,
    StructureProblem,
    load_project_metadata,
    parse_minimum_python_version,
    read_pinned_python_version,
    require_directory,
    require_openspec_scaffolding,
    require_version_at_least,
)


@pytest.fixture(scope="session")
def repository_root(pytestconfig: pytest.Config) -> Path:
    """The repository root, as pytest itself resolved it (design decision D1)."""
    return Path(pytestconfig.rootpath)


def _build_compliant_tree(root: Path) -> Path:
    """Build a synthetic repository that satisfies every structural invariant."""
    for relative_path in REQUIRED_DIRECTORIES:
        (root / relative_path).mkdir(parents=True, exist_ok=True)
    (root / PYPROJECT_FILENAME).write_text(
        '[project]\nname = "synthetic"\nrequires-python = ">=3.12"\n',
        encoding="utf-8",
    )
    (root / PYTHON_VERSION_FILENAME).write_text("3.12\n", encoding="utf-8")
    (root / OPENSPEC_CONFIG_PATH).write_text("schema: spec-driven\n", encoding="utf-8")
    return root


# --- Requirement: Presence of required directories ---------------------------


@pytest.mark.parametrize("relative_path", REQUIRED_DIRECTORIES)
def test_required_directory_is_present(repository_root: Path, relative_path: str) -> None:
    require_directory(repository_root, relative_path)


def test_missing_directory_is_reported(tmp_path: Path) -> None:
    tree = _build_compliant_tree(tmp_path)
    (tree / "src").rmdir()

    with pytest.raises(StructureProblem) as failure:
        require_directory(tree, "src")

    message = str(failure.value)
    assert "missing" in message
    assert "src" in message


def test_path_that_is_not_a_directory_is_distinguished(tmp_path: Path) -> None:
    tree = _build_compliant_tree(tmp_path)
    (tree / "src").rmdir()
    (tree / "src").write_text("", encoding="utf-8")

    with pytest.raises(StructureProblem) as failure:
        require_directory(tree, "src")

    message = str(failure.value)
    assert "not a directory" in message
    assert "missing" not in message


# --- Requirement: Validity of project metadata -------------------------------


def test_project_metadata_is_valid(repository_root: Path) -> None:
    project = load_project_metadata(repository_root)

    assert project["name"]
    assert project["requires-python"]


def test_unparseable_project_configuration_is_reported(tmp_path: Path) -> None:
    tree = _build_compliant_tree(tmp_path)
    (tree / PYPROJECT_FILENAME).write_text("[project\nname = ", encoding="utf-8")

    with pytest.raises(StructureProblem) as failure:
        load_project_metadata(tree)

    assert "could not be parsed" in str(failure.value)


@pytest.mark.parametrize("missing_field", ["name", "requires-python"])
def test_missing_identity_field_is_reported(tmp_path: Path, missing_field: str) -> None:
    tree = _build_compliant_tree(tmp_path)
    declared = {"name": '"synthetic"', "requires-python": '">=3.12"'}
    del declared[missing_field]
    body = "\n".join(f"{key} = {value}" for key, value in declared.items())
    (tree / PYPROJECT_FILENAME).write_text(f"[project]\n{body}\n", encoding="utf-8")

    with pytest.raises(StructureProblem) as failure:
        load_project_metadata(tree)

    assert f"project.{missing_field}" in str(failure.value)


# --- Requirement: Python version consistency ---------------------------------


def test_pinned_version_satisfies_declared_constraint(repository_root: Path) -> None:
    project = load_project_metadata(repository_root)
    minimum = parse_minimum_python_version(project["requires-python"])
    pinned = read_pinned_python_version(repository_root)

    require_version_at_least(pinned, minimum, PYTHON_VERSION_FILENAME)


def test_running_interpreter_satisfies_declared_constraint(repository_root: Path) -> None:
    project = load_project_metadata(repository_root)
    minimum = parse_minimum_python_version(project["requires-python"])
    running = (sys.version_info.major, sys.version_info.minor)

    require_version_at_least(running, minimum, "the running interpreter")


def test_pinned_version_below_minimum_is_reported() -> None:
    with pytest.raises(StructureProblem) as failure:
        require_version_at_least((3, 11), (3, 12), PYTHON_VERSION_FILENAME)

    message = str(failure.value)
    assert "3.11" in message
    assert "3.12" in message


def test_running_interpreter_below_minimum_is_reported() -> None:
    with pytest.raises(StructureProblem) as failure:
        require_version_at_least((3, 9), (3, 12), "the running interpreter")

    message = str(failure.value)
    assert "the running interpreter" in message
    assert "3.9" in message
    assert "3.12" in message


@pytest.mark.parametrize("specifier", ["~=3.12", ">3.12", ">=3", "any"])
def test_unsupported_version_specifier_fails_loudly(specifier: str) -> None:
    with pytest.raises(StructureProblem) as failure:
        parse_minimum_python_version(specifier)

    assert "unsupported" in str(failure.value)


# --- Requirement: Integrity of the OpenSpec scaffolding ----------------------


def test_openspec_scaffolding_is_intact(repository_root: Path) -> None:
    require_openspec_scaffolding(repository_root)


def test_missing_schema_declaration_is_reported(tmp_path: Path) -> None:
    tree = _build_compliant_tree(tmp_path)
    (tree / OPENSPEC_CONFIG_PATH).write_text(
        "# schema: spec-driven\nother: value\n", encoding="utf-8"
    )

    with pytest.raises(StructureProblem) as failure:
        require_openspec_scaffolding(tree)

    assert "no workflow schema" in str(failure.value)


# --- Requirement: Deterministic test collection ------------------------------


def _collect_node_ids(working_directory: Path) -> list[str]:
    """Collect, without running, the tests pytest sees from a working directory."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=working_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return sorted(
        line.strip() for line in completed.stdout.splitlines() if "::" in line
    )


@pytest.mark.slow
def test_collection_is_identical_from_a_subdirectory(repository_root: Path) -> None:
    from_root = _collect_node_ids(repository_root)
    assert from_root, "no tests were collected from the repository root"

    from_subdirectory = _collect_node_ids(repository_root / "tests")

    assert from_subdirectory == from_root
