# Upload a new version

To upload a new version update the version in the [pyproject.toml](./pyproject.toml) file and execute the following command from the terminal:

```bash
python -m build
python -m twine upload --repository pypi dist/*
```
