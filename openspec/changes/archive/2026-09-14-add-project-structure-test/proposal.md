## Why

The repository is at its initial state: git tracks only `.gitignore` and `README.md`, `src/` is an empty directory, there is no `tests/`, and `pyproject.toml` contains no pytest configuration. There is therefore no automated check that the structure the project will rely on actually exists and stays coherent.

A structural test is the cheapest guard-rail to introduce first: it pins the layout contract so that later changes fail loudly instead of drifting silently, and at the same time it verifies end-to-end that the toolchain (uv + pytest) is actually runnable. Doing it now, while the structure is minimal, costs almost nothing; doing it later means writing assertions against a layout that has already grown by accretion.

## What Changes

- New `tests/` directory, discovered automatically by pytest.
- New test module verifying the repository's structural invariants: presence of the required directories, validity and completeness of the project metadata, consistency between the declared Python version and the running environment, integrity of the OpenSpec scaffolding.
- pytest configuration in `pyproject.toml` (`testpaths` and minimal settings) so that collection is deterministic and does not depend on the directory the command is invoked from.

Explicit scope exclusions, to keep the change from widening beyond the request:

- **No** package is created under `src/`. The directory stays empty; the test can therefore assert that `src/` exists as a directory, not that anything is importable. Defining the package is an architectural decision that deserves a change of its own.
- **No** new dependencies are introduced. In particular, `openspec/config.yaml` is verified as text (presence of the file and of the `schema` key) rather than through a YAML parser, because PyYAML is not installed and adding it for a single assertion would degrade the reproducibility of the environment. `tomllib`, by contrast, has been in the standard library since Python 3.11 and carries no cost.
- **No** changes to `main.py`, `README.md`, or product code.
- **No** continuous integration configuration is introduced.

## Capabilities

### New Capabilities

- `project-structure-validation`: automated verification that the required layout elements and toolchain metadata exist and are mutually consistent, failing explicitly when an invariant is violated.

### Modified Capabilities

None. The project has no pre-existing capabilities (`openspec list --specs` reports no specs).

## Impact

- **Files created**: `tests/` and the structural test module inside it.
- **Files modified**: `pyproject.toml`, limited to the pytest configuration section.
- **Dependencies**: none added. `pytest>=9.1.1` is already in the `dev` group; `tomllib` is standard library.
- **Product code**: no impact.
- **Intended side effect**: from this change onward, `uv run pytest` becomes a meaningful command, and any modification that breaks the layout is caught.
- **Recorded constraint**: the invariants that can be asserted today are limited by what exists. Once `src/` hosts a package, the contract will need to be extended by a follow-up change.
