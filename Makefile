

.PHONY=black flake8 mypy test

all: black flake8 mypy test


black:
	black src tests

flake8:
	flake8 --max-line-length 120 src tests

mypy:
	PYTHONPATH=src mypy src

test:
	pytest

