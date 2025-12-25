# Python-Swiss-army-Knife

Python codebase for normal usage.

A small tool kit that is still growing

[DEV Installation]
python -m pip install -e .

[Generating distribution archives]
python3 -m build

[Uploading the distribution archives]
python3 -m pip install --upgrade twine

Note: token use PyPI not TestPyPI
python3 -m twine upload dist/*


[Installing your newly uploaded package]
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps example-package-YOUR-USERNAME-HERE

[Reference]
https://packaging.python.org/en/latest/tutorials/packaging-projects/