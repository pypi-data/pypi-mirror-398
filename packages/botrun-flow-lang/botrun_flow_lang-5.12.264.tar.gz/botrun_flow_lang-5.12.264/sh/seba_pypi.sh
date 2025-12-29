source .venv/bin/activate
python -m build
python -m twine upload dist/*
rm -fr dist
