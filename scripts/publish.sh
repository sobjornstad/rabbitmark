#!/bin/bash
set -e

if [ ! -d "scripts" ]; then
  echo "Please run this script from the root of the repository."
  exit 1
fi

. venv/bin/activate
rm -rf build/
rm -f dist/*
mkdir -p dist
python setup.py sdist bdist_wheel
TWINE_PASSWORD=$(cat .pypi_token) twine upload --username '__token__' dist/*
