# How to build here for

python -m pip install --upgrade pip
python -m pip install --upgrade hatchling
python -m pip install --upgrade twine
python -m pip install --upgrade build
python -m build
python -m twine upload --repository testpypi dist/*

python -m pip freeze > requirements.txt

python -m pip install -r requirements.txt