# Information for Developers

## Publishing to PyPI

You can build the package by running the following command in the same directory as `pyproject.toml`:

```sh
python3 -m build
```

Output should be located in the `dist` directory:

```
dist/
├── jelka-version-something.whl
└── jelka-version.tar.gz
```

To securely upload your project, you’ll need a PyPI API token. It can be created [here](https://test.pypi.org/manage/account/#api-tokens) for TestPyPI, and [here](https://pypi.org/manage/account/#api-tokens) for PyPI.

Run Twine to upload all of the archives under the `dist` directory:

```sh
python3 -m twine upload dist/*
```

You will be prompted for a username and password. For the username, use `__token__`. For the password, use the token value, including the `pypi-` prefix.

## Linting and Testing

Run the following command to install the package locally:

```sh
pip install -e .
```

To run the linter, you can use:

```sh
ruff check
```

To run the formatter, you can use:

```sh
ruff format
```

To typecheck the code, you can use:

```sh
pyright
```
