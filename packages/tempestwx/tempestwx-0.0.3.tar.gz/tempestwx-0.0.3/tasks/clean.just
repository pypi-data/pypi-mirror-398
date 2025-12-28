# run clean tasks
[group('clean')]
clean: clean-build clean-coverage clean-mypy clean-pytest clean-python clean-ruff

# clean build folders
[group('clean')]
clean-build:
    rm -rf dist/

# clean coverage files
[group('clean')]
clean-coverage:
    rm -rf .coverage*

# clean mypy folders
[group('clean')]
clean-mypy:
    rm -rf .mypy_cache/

# clean pytest cache
[group('clean')]
clean-pytest:
    rm -rf .pytest_cache/

# clean python caches
[group('clean')]
clean-python:
    find . -type f -name '*.py[co]' -delete
    find . -type d -name __pycache__ -exec rm -r {} \+

# clean ruff cache
[group('clean')]
clean-ruff:
    rm -rf .ruff_cache/

# clean venv folder
[confirm]
[group('clean')]
clean-venv:
    rm -rf .venv/
