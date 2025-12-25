#!/usr/bin/env bash

echo "build package"
python -m build

echo "upload to pypi"
python -m twine upload dist/*
