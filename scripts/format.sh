#!/bin/sh -e

set -x

black .
isort .
ruff check --fix .
