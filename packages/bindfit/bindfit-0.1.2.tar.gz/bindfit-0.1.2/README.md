# Bindfit: A binding constant fitting library for Python

## Development environment setup with venv

```
# Create and activate venv
python -m venv .venv
source .venv/bin/activate

# Install requirements
./install_dev_requirements.sh

# Set up pre-commit pipeline
pre-commit install
pre-commit run
```

## Development environment setup with Flake

```
direnv allow
```

### Deploying to PyPI

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade build twine
python -m build  # Generate distribution archives
python -m twine upload --repository pypi dist/*  # Upload distribution archives
```
