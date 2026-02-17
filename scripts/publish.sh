#!/bin/bash
set -e

if [ ! -d "scripts" ]; then
  echo "Please run this script from the root of the repository."
  exit 1
fi

rm -rf build/
rm -f dist/*
mkdir -p dist
uv build
UV_PUBLISH_TOKEN=$(cat .pypi_token) uv publish
