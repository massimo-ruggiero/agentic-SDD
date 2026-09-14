## 1. Test toolchain setup

- [x] 1.1 Create the `tests/` directory and verify that `uv run pytest` completes without collection errors (zero tests collected is an acceptable outcome at this step)
- [x] 1.2 Add `[tool.pytest.ini_options]` to `pyproject.toml` with `testpaths = ["tests"]` and the marker registration used by the subprocess test; verify with `uv run pytest --collect-only` that the reported `rootdir` matches the repository root (D1)

## 2. Check infrastructure

- [x] 2.1 Implement each check as a pure function that receives the root to operate on, per D6; verify that no function reads fixed paths and that each can be invoked against an arbitrary root
- [x] 2.2 Declare the contract of required paths as a module-level data structure, per D5; verify that adding an entry produces a newly collected test case without touching any logic
- [x] 2.3 Obtain the repository root in the tests from `pytestconfig.rootpath`, per D1; verify that the suite passes when invoked from the root

## 3. Requirement - Presence of required directories

- [x] 3.1 Parametrised test over the path contract; verify a successful outcome for every path in the real repository
- [x] 3.2 Missing-directory scenario on a synthetic `tmp_path` tree; verify that the failure names the missing path
- [x] 3.3 Scenario where a required path exists as a file on `tmp_path`; verify that the message distinguishes this case from the path being absent

## 4. Requirement - Validity of project metadata

- [x] 4.1 Read `pyproject.toml` with `tomllib` and assert the presence of `name` and `requires-python`; verify a successful outcome against the real repository
- [x] 4.2 Syntactically invalid TOML scenario on `tmp_path`; verify that the failure reports the parsing error rather than propagating a raw exception
- [x] 4.3 Missing identity field scenario on `tmp_path`; verify that the message indicates which of the two fields is missing

## 5. Requirement - Python version consistency

- [x] 5.1 Implement version comparison restricted to the `>=X.Y` subset, failing explicitly on unrecognised specifiers, per D2; verify with unit cases that a specifier outside the subset makes the check fail rather than pass
- [x] 5.2 Assert that the value in `.python-version` satisfies `requires-python`; verify a successful outcome against the repository's current values (`3.12` against `>=3.12`)
- [x] 5.3 Assert that the running interpreter satisfies `requires-python`; verify against synthetic values that a lower version produces a failure reporting both the version and the violated constraint

## 6. Requirement - Integrity of the OpenSpec scaffolding

- [x] 6.1 Verify the presence of `openspec/specs/`, `openspec/changes/` and of the `schema` declaration in `openspec/config.yaml` through a text check, per D3; verify a successful outcome against the real repository
- [x] 6.2 Scenario of a configuration without a schema declaration on `tmp_path`; verify that the failure reports the missing declaration

## 7. Requirement - Deterministic test collection

- [x] 7.1 Subprocess test running `sys.executable -m pytest --collect-only -q` from the root and from a subdirectory, comparing the collected identifiers normalised and sorted, per D4; verify that the two sets match
- [x] 7.2 Mark the test as slow and deselectable; verify that a run excluding the marker does not collect it and that the remaining suite stays green

## 8. Overall verification

- [x] 8.1 Run `uv run pytest` from the repository root and verify that the whole suite passes
- [x] 8.2 Verify requirement-to-test traceability: every requirement in `specs/project-structure-validation/spec.md` is exercised by at least one test, negative scenarios included
- [x] 8.3 Verify that `uv.lock` is unchanged with respect to its state before the change, confirming that no dependency was introduced
