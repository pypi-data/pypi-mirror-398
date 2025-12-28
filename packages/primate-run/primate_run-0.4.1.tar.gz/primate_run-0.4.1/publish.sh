#!/usr/bin/env bash
set -euo pipefail

rm -rf dist/ build/ *.egg-info/
./build.sh
twine upload dist/*
