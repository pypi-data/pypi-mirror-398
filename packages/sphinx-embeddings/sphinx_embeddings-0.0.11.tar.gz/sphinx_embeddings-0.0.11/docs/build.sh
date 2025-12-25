cd docs
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
rm -rf _build
sphinx-build -b html . _build
deactivate
rm -rf .venv
cd ..
