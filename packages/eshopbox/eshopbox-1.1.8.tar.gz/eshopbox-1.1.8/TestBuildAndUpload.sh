# remove
rm -r dist/

# build
python -m build

# upload
twine upload --repository testpypi dist/* --verbose