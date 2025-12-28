# run release tasks
[group('release')]
release:

# bump version (patch, minor, major)
[group('release')]
bump-version level:
    uv version --bump {{level}}

# set to specific version
[group('release')]
set-version version:
    uv version {{version}}

# smoke test wheel
[group('release')]
test-wheel:
    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py

# smoke test source distribution
[group('release')]
test-source:
    uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py

# publish python package
[group('release')]
release-package:
	uv publish
