# cybershuttle-jupyter-kernel

A small example repository that demonstrates a minimal pattern for
implementing a Jupyter-style kernel provisioner and how to integrate it
with a Jupyter server's kernel lifecycle.

This repository includes a sample provisioner, a tiny CLI, and tests. The
sections below show how to build, install, and publish the package (sdist and
wheel), how to test locally, and suggestions for CI publishing.

Quick start
-----------

Install test deps and run the sample provisioner:

```bash
python -m pip install -r requirements.txt
python run_kernel.py run --id demo --mode sample
# press Ctrl-C to stop
```

Run tests:

```bash
PYTHONPATH=. pytest -q
```

Install editable (developer workflow):

```bash
python -m pip install -e .
```

Packaging and build instructions
-------------------------------

Below are step-by-step packaging commands for macOS/zsh. They create an sdist
and a wheel in `dist/`, validate them, and show how to install and (optionally)
upload to TestPyPI/PyPI.

1) Create and activate a build virtual environment (recommended)

```bash
python -m venv .venv-build
source .venv-build/bin/activate
python -m pip install --upgrade pip
```

2) Install build tools

```bash
python -m pip install --upgrade build twine
```

3) Ensure `pyproject.toml` contains a proper project name and version

Open `pyproject.toml` and set `project.version` (for example `0.1.0`) and
confirm `project.name` is the package name you want to publish. Example:

```toml
[project]
name = "cybershuttle-kernel-example"
version = "0.1.0"
requires-python = ">=3.8"
description = "Example kernel provisioner package"
readme = "README.md"
authors = [{ name = "cyber-shuttle" }]
```

4) Build sdist and wheel

```bash
python -m build --sdist --wheel
# artifacts are in ./dist
ls -l dist/
```

5) Validate artifacts

```bash
python -m twine check dist/*
```

6) Install locally from the wheel to test the installed package

```bash
python -m pip install dist/*.whl
python -c "import cybershuttle_kernel; print('ok', getattr(cybershuttle_kernel, '__all__', None))"
```

7) Publish to TestPyPI (recommended first)

- Create a TestPyPI account at https://test.pypi.org/account/register/ and
  get an API token.
- Upload:

```bash
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

- Install from TestPyPI to verify:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps cybershuttle-kernel-example
```

8) Publish to PyPI (when ready)

```bash
python -m twine upload dist/*
```

9) Cleanup build artifacts (optional)

```bash
rm -rf build dist *.egg-info
```

Common issues and troubleshooting
---------------------------------

- Missing build tools: run `python -m pip install --upgrade build setuptools wheel`.
- pyproject metadata errors: `twine check` will point out missing/invalid fields.
- Versioning: ensure `project.version` is updated for each release.
- Package name: the installable package name comes from `project.name` in
  `pyproject.toml`, not the repository name.
- Editable vs built package: `pip install -e .` is for local development. For
  distribution, create the wheel and sdist and upload.

Continuous integration (optional)
--------------------------------

You can add a GitHub Actions workflow to run tests and publish on tags. The
workflow commonly:

- runs tests on push/PR,
- builds artifacts on tag, and
- uploads to PyPI using a repository secret for `TWINE_USERNAME` and `TWINE_PASSWORD` (or `TWINE_API_TOKEN`).

If you'd like, I can add a sample `.github/workflows/publish.yml` that:

- runs pytest,
- builds artifacts,
- uploads to TestPyPI on a `test-*` tag and to PyPI on a release tag.

Security and best practices
---------------------------

- Use TestPyPI for initial verification to avoid polluting the real PyPI.
- Use API tokens for Twine uploads; store them as encrypted secrets in CI.
- Pin your development dependencies where appropriate.

If you want me to run a local build here and show the created `dist/` files,
I can do that (I won't upload to PyPI without credentials). Tell me if you'd
like me to run the build now.
