# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Nothing yet.

## [0.3.0] - 2025-12-22
### Added
- Manual path for both statusGUI and pySetupH5 if dataset outside of /data/visitor folder.
- `clean_dir_name` helper (mirroring MATLAB `gtCleanDirName`) to normalise GPFS/mnt paths before deriving ESRF metadata; includes pytest coverage for visitor-root handling.
- Programmatic presets for `pySetupH5.setup_pre_processing`, allowing dict/sequence configs and surfacing missing dataset errors directly in the widget.

### Changed
- DCT database probing now seeds graindb defaults, honours MySQL env vars/`~/.my.cnf`, and can fall back to SQLAlchemy/MySQL drivers when `DB.h5` is absent.
- Base install depends on `mysqlclient` for SQL checks and moves `Dans-Diffraction` to the optional `extra` bundle.
- Visitor-root processing refreshes status objects against the latest acquisition folder instead of the parent date directory for DCT/PCT/FF/s3DXRD flows.

## [0.2.0] - 2025-11-04
### Added
- Targeted mypy enforcement for the post-processing pipeline and dedicated documentation on running the developer toolchain locally.
- Added `esrf-pathlib` as a core dependency and implemented `set_permissions_recursive` to manage visitor-folder permissions safely.
- Reworked tests case unit using pytest. The code passes all test, manual and pytest. Ready for new TAG
- Setup checking pipeline of [dev] to run pre-commit checks automatically
- Dedicated `esrf_statusgui.file_utils.paths` module to normalise visitor-root handling and expose `esrf-pathlib` metadata (proposal, beamline, session date) to the rest of the codebase.
- Extensive pytest suite covering the CLI entry point, status widgets, and the refactored brain modules (`post_process`, `source_experiment`, `structure`), plus an ID11 sample notebook fixture.
- Ruff configuration, `.flake8`, and CI scaffolding to enforce formatting and linting consistently.
### Changed
- Bundle DCT tutorial notebooks within `esrf_statusgui` and resolve them via `importlib.resources`, removing the dependency on a local DCT git checkout.
- Update the DCT MATLAB connector to require an already running, shared MATLAB engine session (e.g. launched after `module load dct`) instead of spawning MATLAB locally.
- Typed the tomography, FF, and s3DXRD status components and hardened widget observer handling to surface errors instead of silently failing.
- Trimmed the pre-commit configuration to the essential hooks (black, ruff, flake8, mypy, bandit) and aligned repository instructions with the enforced checks.
- Relaxed legacy test modules with explicit `allow-untyped-defs` pragmas to keep static analysis focused on maintained code paths.
- Reorganised the package into a modern `src/` layout, refreshed `pyproject.toml` with optional extras (`dev`, `gui`, `full`, `all`), and streamlined packaging metadata for editable installs.
- Major refresh of the ipywidgets GUI: `DatasetSelectionTab` now delegates to `DatasetSelectionLogic`, adds natural sorting, dataset refresh, per-method accordions, and colour-coded processing states.
- Hardened `Post_process` orchestration and DCT helper modules (parameter loading, dataset browser, experiment logic) to better validate data and expose richer widgets.
- Logging and import hygiene pass throughout the codebase; centralised ESRFPath fallback handling.

### Removed

- Legacy `StatusGUI` namespace package, old notebook helpers, and egg metadata replaced by the new structured package and tooling.

## [0.1.0] - 2025-09-10

### Added

- Initial public release of the ESRF ID11 Status GUI.
- ipywidgets dashboard for browsing ESRF visitor data (`/data/visitor/<proposal>/<beamline>/<date>`) and inspecting DCT, tomography, FF, and s3DXRD processing states.
- Post-processing toolbar with notebook generation helpers, dataset utilities, and support scripts for experiment folder bootstrapping.

[unreleased]: https://gitlab.esrf.fr/graintracking/statusgui/-/compare/v0.3.0...HEAD
[0.3.0]: https://gitlab.esrf.fr/graintracking/statusgui/-/compare/v0.2.0...v0.3.0
[0.2.0]: https://gitlab.esrf.fr/graintracking/statusgui/-/compare/v0.1.0...v0.2.0
[0.1.0]: https://gitlab.esrf.fr/graintracking/statusgui/-/tags/v0.1.0
