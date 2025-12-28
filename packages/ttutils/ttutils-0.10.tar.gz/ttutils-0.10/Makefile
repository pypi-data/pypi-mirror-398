clean:
	rm -fr dist/ *.eggs .eggs build/ .coverage htmlcov/ .mypy_cache/ .pytest_cache/ *.log *.egg-info
	find . -name '__pycache__' | xargs rm -rf
	find . -name '*.pyc' | xargs rm -rf

test:
	pip install .\[dev\]
	ruff check .
	pytest tests

mypy:
	pip install mypy
	mypy --install-types --non-interactive ttutils

release: clean
	uv pip install twine build
	python -m build --sdist --wheel .
	python -m twine upload dist/*
