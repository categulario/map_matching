.PHONY: pytest lint test

test: pytest lint

pytest:
	pytest -xvv

lint:
	flake8 --exclude=.env,.tox,dist,docs,build,*.egg,.venv .
