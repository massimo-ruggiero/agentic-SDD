# Project Structure Validation Specification

## Purpose

Provides an automated, repeatable check of the repository's structural contract, so that a missing or inconsistent layout element or toolchain metadata value is detected immediately and explicitly, instead of surfacing later as an obscure error during development.

## Requirements

### Requirement: Presence of required directories

The validation SHALL verify that every directory required by the project's structural contract exists and is in fact a directory. When one of them is missing, the validation MUST fail and MUST identify which element is absent.

#### Scenario: All required directories are present

- **WHEN** the validation runs against a repository in which every required directory exists
- **THEN** the directory check succeeds

#### Scenario: A required directory is absent

- **WHEN** the validation runs and one of the required directories does not exist
- **THEN** the validation fails
- **AND** the failure message reports the path of the missing directory

#### Scenario: A required path exists but is not a directory

- **WHEN** a required path exists as a file rather than as a directory
- **THEN** the validation fails, distinguishing this case from the path being absent

### Requirement: Validity of project metadata

The validation SHALL verify that the project configuration file exists, is syntactically valid, and declares the minimum required identity fields, namely the project name and the supported Python version constraint.

#### Scenario: Complete and valid metadata

- **WHEN** the project configuration file is syntactically valid and declares both the name and the Python version constraint
- **THEN** the metadata check succeeds

#### Scenario: Configuration file cannot be parsed

- **WHEN** the project configuration file is not syntactically valid
- **THEN** the validation fails, reporting the parsing error

#### Scenario: Missing identity field

- **WHEN** the configuration file is valid but one of the required identity fields is not declared
- **THEN** the validation fails, indicating which field is missing

### Requirement: Python version consistency

The validation SHALL verify that both the Python version pinned for the development environment and the interpreter actually running satisfy the version constraint declared in the project metadata. Any divergence between the declared version, the pinned version, and the running version MUST be reported as a failure.

#### Scenario: Pinned version consistent with the declared constraint

- **WHEN** the Python version pinned for the environment satisfies the constraint declared in the metadata
- **THEN** the consistency check succeeds

#### Scenario: Pinned version below the required minimum

- **WHEN** the Python version pinned for the environment is lower than the minimum declared in the metadata
- **THEN** the validation fails, reporting both values side by side

#### Scenario: Running interpreter does not comply

- **WHEN** the suite runs under an interpreter that does not satisfy the declared version constraint
- **THEN** the validation fails, reporting the interpreter version and the violated constraint

### Requirement: Integrity of the OpenSpec scaffolding

The validation SHALL verify that the repository's OpenSpec scaffolding is intact, namely that the specs directory, the changes directory, and the configuration file exist, and that the latter declares a workflow schema.

#### Scenario: Scaffolding is intact

- **WHEN** the specs and changes directories exist and the configuration file declares a schema
- **THEN** the scaffolding check succeeds

#### Scenario: No workflow schema declared

- **WHEN** the OpenSpec configuration file exists but declares no workflow schema
- **THEN** the validation fails, reporting the missing declaration

### Requirement: Deterministic test collection

The validation SHALL be collected and executed identically regardless of the working directory it is invoked from, provided that directory lies inside the repository, so that the outcome does not depend on the point of invocation.

#### Scenario: Invocation from a subdirectory

- **WHEN** the suite is invoked from a subdirectory of the repository rather than from the root
- **THEN** the same set of tests is collected as would be collected from the root
- **AND** the validation outcome is the same
