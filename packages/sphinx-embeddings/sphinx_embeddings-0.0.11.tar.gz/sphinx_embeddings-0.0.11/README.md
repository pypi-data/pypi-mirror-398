# sphinx-embeddings

Embeddings-powered features for Sphinx projects

## Setup

```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Build

```
python3 -m build
```

## Distribute

```
python3 -m twine upload --repository testpypi dist/*
python3 -m twine upload dist/*
`````
