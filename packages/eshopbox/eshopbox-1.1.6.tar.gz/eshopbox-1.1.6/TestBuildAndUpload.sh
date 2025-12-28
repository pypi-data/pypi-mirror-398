# remove
rm -rf dist/

# build
python -m build

# upload
twine upload --repository testpypi dist/* --verbose