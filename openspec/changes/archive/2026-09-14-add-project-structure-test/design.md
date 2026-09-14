## Context

See `proposal.md` - Why for the motivation. The requirements live in `specs/project-structure-validation/spec.md`.

Three constraints of the current environment drive the approach and must be considered together:

- `pytest 9.1.1` is the only development dependency; `packaging` is **not** installed, so no PEP 440 specifier parser is available in the environment.
- `PyYAML` is **not** installed, so `openspec/config.yaml` cannot be parsed as YAML without adding a dependency.
- `tomllib` has been in the standard library since Python 3.11, so `pyproject.toml` can be parsed at no cost.

The proposal explicitly rules out adding dependencies. The decisions below are largely a consequence of that constraint.

## Goals / Non-Goals

**Goals:**

- Every violated invariant produces a failure that identifies the offending element on its own, without forcing the reader to open the test code to understand what is broken.
- The structural contract is extended by adding data, not by modifying logic.
- No silent false positives: if a check cannot reach a verdict, it fails rather than passing.

**Non-Goals:**

- No general-purpose validation reusable across other repositories is designed here: the contract is specific to this project.
- The *semantic* content of the OpenSpec artifacts is not validated, only the presence of the scaffolding.

## Decisions

### D1 - The repository root comes from pytest, it is not recomputed

The validation needs an absolute reference point to resolve the required paths. It uses the `rootpath` that pytest already computes, exposed to tests through the `request` fixture (or `pytestconfig`).

*Alternatives considered:* walking up from `__file__` looking for `pyproject.toml` duplicates logic pytest performs anyway, and in a nested checkout it can walk past the intended root; a fixed relative path such as `../` breaks as soon as the test file is moved.

*Relevant consequence:* pytest's `rootdir` is deterministic only when a recognised configuration section exists. The `[tool.pytest.ini_options]` section in `pyproject.toml` therefore does more than pin `testpaths`: it is also what anchors `rootdir` to the repository root. The two must be introduced together.

### D2 - Version comparison implements the PEP 440 subset actually in use, and fails on the rest

`requires-python` is a PEP 440 specifier. Interpreting it in general requires `packaging`, which the proposal rules out. Only the subset actually present in the project (`>=X.Y`) is implemented, comparing tuples of integers.

*Alternatives considered:* adding `packaging` would solve the general case, but it introduces a dependency for a single assertion and degrades the reproducibility of the environment; accepting any specifier without interpreting it would make the check vacuous.

*The constraint that makes this safe:* when the specifier falls outside the supported subset, the validation **fails** with a message asking for the comparison to be extended. It does not pass silently. This is what prevents the simplification from turning into a false positive the day `requires-python` becomes more elaborate.

### D3 - `config.yaml` is verified as text, with the limitation stated

The OpenSpec scaffolding requirement concerns the presence of a schema declaration. It is checked with a line-level text check, without a YAML parser.

*Alternatives considered:* adding `PyYAML` would allow the file's syntax to be genuinely validated, but it is a dependency introduced for an incidental check.

*Limitation accepted deliberately:* a text check does not detect a syntactically invalid YAML file. This is not a theoretical risk - it has already happened in this repository that a malformed `config.yaml` was silently discarded by OpenSpec, which then behaved as if the file were absent. A text check would not have caught that case. See the Risks section.

### D4 - Collection determinism is verified in a subprocess, with `--collect-only` and `sys.executable`

The determinism requirement calls for comparing what gets collected when the suite is invoked from the root and from a subdirectory. This cannot be expressed within a single process: it requires a genuine second invocation. The implementation runs `sys.executable -m pytest --collect-only -q` under two different working directories and compares the collected identifiers, normalised and sorted.

*Alternatives considered:* merely asserting that `testpaths` is configured would check the presumed cause instead of the effect, and that is precisely the kind of test that keeps passing once the behaviour breaks; invoking `uv run pytest` would introduce a runtime dependency on `uv` being on PATH, whereas `sys.executable` uses the same interpreter as the suite by construction.

`--collect-only` avoids recursion: the subprocess lists the tests, it does not run them.

### D5 - The structural contract is parametrised data, not a sequence of assertions

The required paths are declared in a single module-level data structure and consumed through `pytest.mark.parametrize`, so that each path is an independent test case.

*Alternatives considered:* a single test asserting all paths in sequence stops at the first failure and hides the rest, violating the requirement that the failure identify the missing element - it would identify only one per run.

### D6 - Checks are pure functions over a root, to make the negative scenarios exercisable

A large share of the scenarios in the spec describe how the validation behaves *when an invariant is violated*: a missing directory, an unparseable configuration file, a pinned version below the minimum. None of these cases can be exercised against the real repository, which is compliant by construction: a test that only asserted against the repository would leave roughly half of the spec uncovered.

Each check is therefore implemented as a function that receives the root to operate on and returns a verdict, and is exercised twice: once against the real repository, to confirm current compliance, and once against synthetic trees built with the `tmp_path` fixture, for the violation scenarios.

*Alternatives considered:* asserting directly in the test bodies against fixed paths is shorter to write, but it makes the negative scenarios unverifiable and reduces the contract to its positive half only.

## Risks / Trade-offs

- **The text check on `config.yaml` does not detect invalid YAML** → Limitation stated in D3 and already observed concretely in this repository. Mitigation: none within the scope of this change, given the dependency constraint. Once a YAML dependency is justified by other needs of the project, the check should be strengthened; until then the requirement covers the presence of the declaration, not the validity of the file.

- **The supported PEP 440 subset is minimal** → Mitigated by the explicit failure on unrecognised specifiers (D2), which turns a potential false positive into a visible error.

- **The subprocess test is noticeably slower than the others and depends on the execution environment** → Mitigation: use `sys.executable` rather than `uv`, restrict it to `--collect-only`, and mark the test so it can be deselected when a fast run is needed.

- **The contract asserts against an empty `src/`** → The value of the `src/` check stays low until a package exists. This is a known limitation recorded in the proposal, not a flaw in the design: extending the contract is a matter for a follow-up change.

- **A structural contract can make the project rigid** → If the layout changes legitimately, the test fails and must be updated. That is the intended cost of an explicit contract; D5 reduces it to a one-line data edit.

## Open Questions

- Whether and when to run this suite in continuous integration. The answer affects neither the requirements, nor the approach, nor the task breakdown, and can be given once the project has a CI pipeline.
