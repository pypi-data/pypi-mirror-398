# Publishing to PyPI

`setuptools-scm` drives the package version from Git tags. Create an annotated
release tag (e.g. `v0.4.0`) before building so wheels/sdists carry the correct
version and no local suffix is added (`local_scheme = "no-local-version"`).

## Prerequisites

- Clean working tree with tests/linting passing.
- Python 3.10+ and the build tooling installed: `pip install -e ".[dev]"` or
  `pip install build twine`.
- Remove old artifacts: `rm -rf dist/ build/`.

## Release steps

1. Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"` and push the tag.
2. Build artifacts locally:

   ```bash
   python -m build
   ```

3. Verify metadata:

   ```bash
   twine check dist/*
   ```

4. Upload to TestPyPI first (recommended), then PyPI:

   ```bash
   twine upload --repository testpypi dist/*
twine upload dist/*
```

5. Smoke-test the published wheel:

   ```bash
pip install --index-url https://pypi.org/simple "esrf-statusgui[gui]"
statusgui --help  # entry point is provided as both statusgui/statusGUI
```

PyPI/TestPyPI reject direct Git dependencies in `requires_dist`. Ensure
`esrf-loadfile` is published to PyPI (and referenced with a normal version
specifier) before building release artifacts, and avoid non-PyPI sources in
`pyproject.toml`. The ESRF `dct` package is not yet on PyPI; the `[extra]`
extra that pulls it will fail when installed from TestPyPI/PyPI. Publish `dct`
first (or omit the extra) before uploading a release intended for users.
